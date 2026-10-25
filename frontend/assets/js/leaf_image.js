/**
 * LEAF_AI — Tiền xử lý & kiểm tra chất lượng ảnh lá ngay trên trình duyệt
 * - Chuẩn hoá: xoay theo EXIF (trình duyệt tự áp dụng khi vẽ), thu nhỏ cạnh dài ≤ 1280px, nén JPEG
 *   → ảnh gửi đi ~150–400 KB, nhanh trên mạng 4G và dưới giới hạn 4.5 MB của Vercel.
 * - Đo chất lượng trên bản 256px: độ sáng, cháy sáng, độ nét (phương sai Laplacian), tỉ lệ điểm ảnh là lá.
 * Toàn bộ chạy bất đồng bộ (Promise), không chặn giao diện.
 */
(function (global) {
  'use strict';

  const MAX_SIDE = 1280;
  const JPEG_QUALITY = 0.86;
  const ANALYZE_SIDE = 256;

  // Ngưỡng hiệu chỉnh trên ảnh lá vải thật: gốc / làm mờ σ=1.5 và σ=4 / tối 30% / sáng 220% / thu nhỏ 250px
  const T = {
    minSide: 320,
    darkMean: 55,
    darkPct: 0.55,
    brightPct: 0.15,
    brightMean: 205,
    blurVar: 350,     // phương sai Laplacian (ảnh 256px) dưới ngưỡng này: ảnh mờ — ảnh nét thật đo được 950–7400
    blurSevere: 120,
    leafMin: 0.15     // dưới 15% điểm ảnh là mô lá: lá quá nhỏ / không có lá
  };

  const MESSAGES = {
    low_resolution: 'Ảnh có độ phân giải thấp — chụp gần hơn để lá chiếm phần lớn khung hình.',
    too_dark: 'Ảnh hơi tối — chụp dưới ánh sáng tự nhiên, tránh bóng râm đậm.',
    overexposed: 'Ảnh bị cháy sáng — tránh nắng gắt chiếu thẳng, nghiêng lá để giảm loá.',
    blurry: 'Ảnh bị mờ — giữ máy chắc tay, chạm vào lá trên màn hình để lấy nét rồi chụp.',
    no_leaf: 'Không thấy rõ lá — đưa lá vào giữa khung, chiếm khoảng 60–80% ảnh.'
  };

  function loadImage(src) {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.decoding = 'async';
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error('Không đọc được ảnh. Hãy chọn ảnh JPG, PNG hoặc WebP khác.'));
      img.src = src;
    });
  }

  function makeCanvas(w, h) {
    const c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    return c;
  }

  /** RGB (0–255) → [h (0–360), s (0–1), v (0–1)] */
  function rgbToHsv(r, g, b) {
    const max = Math.max(r, g, b);
    const min = Math.min(r, g, b);
    const d = max - min;
    let h = 0;
    if (d) {
      if (max === r) h = ((g - b) / d) % 6;
      else if (max === g) h = (b - r) / d + 2;
      else h = (r - g) / d + 4;
      h *= 60;
      if (h < 0) h += 360;
    }
    return [h, max ? d / max : 0, max / 255];
  }

  /**
   * Điểm ảnh "có thể là mô lá vải": xanh lá (khỏe), vàng/nâu (vết bệnh, cháy lá),
   * đỏ đồng (lộc non, nhung nhện). Loại nền trắng/xám/đen và trời xanh dương.
   */
  function isLeafPixel(r, g, b) {
    const [h, s, v] = rgbToHsv(r, g, b);
    if (v < 0.12 || s < 0.16) return false;
    if (h >= 35 && h <= 170) return true;                  // vàng-xanh → xanh lá
    if ((h < 35 || h >= 340) && s > 0.25 && v < 0.9) return true; // nâu, đỏ đồng
    return false;
  }

  function analyzePixels(imageData, w, h) {
    const px = imageData.data;
    const n = w * h;
    const gray = new Float32Array(n);
    let sum = 0;
    let dark = 0;
    let bright = 0;
    let leaf = 0;

    for (let i = 0, p = 0; i < n; i++, p += 4) {
      const r = px[p], g = px[p + 1], b = px[p + 2];
      const y = 0.299 * r + 0.587 * g + 0.114 * b;
      gray[i] = y;
      sum += y;
      if (y < 30) dark++;
      if (y > 245) bright++;
      if (isLeafPixel(r, g, b)) leaf++;
    }

    // Phương sai Laplacian (kernel 4 lân cận) — thước đo độ nét kinh điển
    let lapSum = 0;
    let lapSq = 0;
    let count = 0;
    for (let y = 1; y < h - 1; y++) {
      for (let x = 1; x < w - 1; x++) {
        const i = y * w + x;
        const lap = gray[i - w] + gray[i + w] + gray[i - 1] + gray[i + 1] - 4 * gray[i];
        lapSum += lap;
        lapSq += lap * lap;
        count++;
      }
    }
    const lapMean = count ? lapSum / count : 0;
    const sharpness = count ? lapSq / count - lapMean * lapMean : 0;

    return {
      mean: sum / n,
      darkPct: dark / n,
      brightPct: bright / n,
      sharpness,
      leafRatio: leaf / n
    };
  }

  function judge(metrics, w0, h0) {
    const issues = [];
    const add = (code, severe = false) => issues.push({ code, severe, message: MESSAGES[code] });

    if (Math.min(w0, h0) < T.minSide) add('low_resolution', Math.min(w0, h0) < 200);
    if (metrics.mean < T.darkMean || metrics.darkPct > T.darkPct) add('too_dark', metrics.mean < 35);
    if (metrics.brightPct > T.brightPct || metrics.mean > T.brightMean) add('overexposed', metrics.brightPct > 0.5);
    if (metrics.sharpness < T.blurVar) add('blurry', metrics.sharpness < T.blurSevere);
    if (metrics.leafRatio < T.leafMin) add('no_leaf', metrics.leafRatio < 0.06);

    const penalty = issues.reduce((a, i) => a + (i.severe ? 35 : 15), 0);
    return {
      score: Math.max(0, 100 - penalty),
      ok: !issues.some((i) => i.severe),
      issues,
      metrics: {
        brightness: Math.round(metrics.mean),
        dark_pct: Math.round(metrics.darkPct * 100),
        bright_pct: Math.round(metrics.brightPct * 100),
        sharpness: Math.round(metrics.sharpness),
        leaf_pct: Math.round(metrics.leafRatio * 100)
      }
    };
  }

  /**
   * Chuẩn bị ảnh để chẩn đoán.
   * @param {string} src data URL hoặc đường dẫn cùng origin
   * @returns {Promise<{dataUrl:string,width:number,height:number,originalWidth:number,originalHeight:number,quality:object}>}
   */
  async function prepare(src) {
    const img = await loadImage(src);
    const w0 = img.naturalWidth;
    const h0 = img.naturalHeight;
    if (!w0 || !h0) throw new Error('Ảnh rỗng hoặc bị hỏng.');

    // 1) Ảnh gửi lên AI
    const scale = Math.min(1, MAX_SIDE / Math.max(w0, h0));
    const w = Math.max(1, Math.round(w0 * scale));
    const h = Math.max(1, Math.round(h0 * scale));
    const out = makeCanvas(w, h);
    const octx = out.getContext('2d');
    octx.imageSmoothingQuality = 'high';
    octx.drawImage(img, 0, 0, w, h);
    const dataUrl = out.toDataURL('image/jpeg', JPEG_QUALITY);

    // 2) Bản nhỏ để đo chất lượng
    const s = Math.min(1, ANALYZE_SIDE / Math.max(w0, h0));
    const aw = Math.max(8, Math.round(w0 * s));
    const ah = Math.max(8, Math.round(h0 * s));
    const ac = makeCanvas(aw, ah);
    const actx = ac.getContext('2d', { willReadFrequently: true });
    actx.drawImage(img, 0, 0, aw, ah);
    const metrics = analyzePixels(actx.getImageData(0, 0, aw, ah), aw, ah);

    return {
      dataUrl,
      width: w,
      height: h,
      originalWidth: w0,
      originalHeight: h0,
      bytes: Math.round((dataUrl.length - dataUrl.indexOf(',') - 1) * 0.75),
      quality: judge(metrics, w0, h0)
    };
  }

  global.LeafImage = { prepare, thresholds: T, _analyzePixels: analyzePixels, _judge: judge };
})(window);

/**
 * LEAF_AI — Vercel Serverless Function: POST /api/diagnose
 * Chẩn đoán bệnh lá vải thiều bằng Google Gemini Vision (structured JSON output).
 *
 * Biến môi trường:
 *   GEMINI_API_KEY        (bắt buộc)
 *   GEMINI_VISION_MODEL   (tuỳ chọn, mặc định gemini-2.5-flash; muốn chính xác hơn dùng gemini-2.5-pro)
 *   GEMINI_VISION_FALLBACK(tuỳ chọn, model dự phòng khi model chính quá tải, mặc định gemini-2.5-flash-lite)
 *   DIAGNOSE_VOTES        (tuỳ chọn, 1–3: số lượt phân tích độc lập để lấy trung bình, mặc định 1)
 *
 * Request : { images: string[] (data URL JPEG/PNG/WebP, 1–3 ảnh cùng một lá), context?: { surface?: 'top'|'bottom'|'both', note?: string } }
 * Response: xem hàm buildResult()
 */

const CLASSES = ['Healthy', 'Anthracnose', 'Downy_blight', 'Leaf_blight', 'Algal_spot', 'Erinose', 'Other'];
const QUALITY_ISSUES = ['blurry', 'too_dark', 'overexposed', 'too_far', 'leaf_cut_off', 'heavy_shadow', 'glare', 'low_resolution', 'cluttered_background'];
const MAX_IMAGES = 3;
const MAX_IMAGE_BYTES = 3_000_000; // sau base64-decode
const UPSTREAM_TIMEOUT_MS = 50_000;

const SYSTEM_PROMPT = `Bạn là chuyên gia bệnh cây (plant pathologist) về cây vải thiều (Litchi chinensis) vùng Lục Ngạn, Bắc Giang.
Nhiệm vụ: phân tích ảnh lá do nông dân chụp và trả về JSON đúng schema. Hãy quan sát kỹ trước khi kết luận.

BƯỚC 1 — XÁC NHẬN ĐỐI TƯỢNG
- Lá vải: lá kép lông chim 2–4 đôi lá chét; lá chét hình mác/thuôn dài, mép nguyên, đầu nhọn; mặt trên xanh đậm bóng, mặt dưới xanh nhạt hơi xám. Lộc non có màu đỏ đồng/nâu đỏ — đây là màu TỰ NHIÊN, KHÔNG phải bệnh.
- Dễ nhầm với lá nhãn (lá chét đầu tù hơn, mặt lá kém bóng). Không chắc thì để lychee_confidence ở mức trung bình.
- Nếu ảnh không phải lá cây, hoặc là lá cây khác rõ ràng: is_lychee_leaf=false và cho Other cao.

BƯỚC 2 — CHẤT LƯỢNG ẢNH: ghi các vấn đề thực sự ảnh hưởng tới chẩn đoán (mờ, tối, cháy sáng, chụp quá xa, lá bị cắt, bóng đổ, loá, độ phân giải thấp, nền rối).

BƯỚC 3 — CHẨN ĐOÁN (6 lớp + Other). Dấu hiệu phân biệt:
1. Anthracnose (Thán thư, Colletotrichum gloeosporioides): đốm nâu RIÊNG LẺ hình tròn/bất định, viền nâu sẫm, thường có QUẦNG VÀNG; khi ẩm có chấm đen nhỏ XẾP VÒNG ĐỒNG TÂM; hay gặp lá non, lá bánh tẻ; nặng thì lộc quăn đen.
2. Leaf_blight (Cháy lá, Pestalotiopsis spp.): vết cháy bắt đầu từ CHÓP hoặc MÉP lá rồi lan liên tục vào phía gân chính; ranh giới với phần xanh là VIỀN NÂU SẪM GỢN SÓNG; mô chết màu xám nâu, khô giòn; chấm đen nhỏ rải rác (không xếp vòng rõ). Phân biệt thán thư: cháy lá là dải liên tục từ mép/chóp, thán thư là đốm riêng lẻ có quầng vàng.
3. Downy_blight (Sương mai, Peronophythora litchii): trên LÁ NON mềm có vết ÚNG NƯỚC xanh xám, hình bất định, từ mép lá, lan nhanh rồi chuyển nâu sẫm; khi ẩm có LỚP MỐC TRẮNG MỊN; mô thối mềm, không khô giòn.
4. Algal_spot (Đốm rong, Cephaleuros virescens): nhiều ĐỐM TRÒN NHỎ 2–5 mm, HƠI NỔI, ở MẶT TRÊN lá già; màu xám xanh rồi CAM/ĐỎ GẠCH như nhung; đốm rải rác hoặc thành cụm, không lan thành mảng lớn từ mép.
5. Erinose (Nhện lông nhung, Aceria litchii): MẶT DƯỚI lá có MẢNG LÔNG NHUNG trắng bạc → vàng nâu → nâu đỏ; mặt trên tương ứng PHỒNG RỘP; lá xoăn, biến dạng. Phân biệt đốm rong: nhung của nhện là mảng lớn ở mặt dưới làm lá biến dạng.
6. Healthy (Khỏe): lá xanh đều, không có tổn thương bệnh lý. Vài vết xước nhỏ, bụi bẩn, lá già hơi ngả màu đều không tính là bệnh.
7. Other: vấn đề KHÔNG thuộc 5 bệnh trên — cháy nắng (vùng bạc/nâu nhạt ở phần lá phơi nắng, không viền sẫm), cháy do thuốc/phân (đốm cháy hình giọt, đều), thiếu dinh dưỡng (vàng đều hoặc vàng giữa gân), sâu ăn lá (lỗ khuyết, mép bị gặm), rệp/muội đen (lớp đen phủ bề mặt), hoặc ảnh không phải lá vải.

QUY TẮC CHO ĐIỂM (scores, số nguyên 0–100, tổng = 100):
- Phản ánh đúng mức độ chắc chắn. Chỉ cho ≥ 85 khi triệu chứng điển hình và nhìn rõ. Ảnh kém hoặc triệu chứng không điển hình thì phân bổ điểm cho các lớp có khả năng.
- Có thể nhiễm 2 bệnh cùng lúc: khi đó cả hai lớp đều có điểm đáng kể.
- Không đoán bệnh khi không thấy tổn thương: lá sạch thì Healthy cao.

KHOANH VÙNG (lesions): tối đa 8 vết rõ nhất, box_2d = [ymin, xmin, ymax, xmax] chuẩn hoá 0–1000 theo ẢNH ĐẦU TIÊN. Lá khỏe thì để mảng rỗng.
affected_area_percent: ước lượng % diện tích lá chét bị tổn thương (0–100).
observed_symptoms, reasoning, retake_advice: viết TIẾNG VIỆT ngắn gọn, dễ hiểu cho nông dân. reasoning nêu vì sao chọn bệnh chính và vì sao loại bệnh dễ nhầm. retake_advice để chuỗi rỗng nếu ảnh đủ tốt.`;

const RESPONSE_SCHEMA = {
  type: 'OBJECT',
  properties: {
    is_plant_leaf: { type: 'BOOLEAN' },
    is_lychee_leaf: { type: 'BOOLEAN' },
    lychee_confidence: { type: 'INTEGER', description: '0-100' },
    subject: { type: 'STRING', description: 'Mô tả ngắn đối tượng trong ảnh (tiếng Việt)' },
    leaf_surface: { type: 'STRING', enum: ['top', 'bottom', 'both', 'unknown'] },
    quality_ok: { type: 'BOOLEAN' },
    quality_issues: { type: 'ARRAY', items: { type: 'STRING', enum: QUALITY_ISSUES } },
    scores: {
      type: 'OBJECT',
      properties: Object.fromEntries(CLASSES.map((c) => [c, { type: 'INTEGER' }])),
      required: CLASSES,
      propertyOrdering: CLASSES
    },
    primary: { type: 'STRING', enum: CLASSES },
    affected_area_percent: { type: 'INTEGER' },
    observed_symptoms: { type: 'ARRAY', items: { type: 'STRING' } },
    reasoning: { type: 'STRING' },
    lesions: {
      type: 'ARRAY',
      items: {
        type: 'OBJECT',
        properties: {
          label: { type: 'STRING', enum: CLASSES },
          box_2d: { type: 'ARRAY', items: { type: 'INTEGER' } }
        },
        required: ['label', 'box_2d']
      }
    },
    retake_advice: { type: 'STRING' }
  },
  required: ['is_plant_leaf', 'is_lychee_leaf', 'lychee_confidence', 'subject', 'leaf_surface', 'quality_ok', 'quality_issues', 'scores', 'primary', 'affected_area_percent', 'observed_symptoms', 'reasoning', 'lesions', 'retake_advice'],
  propertyOrdering: ['is_plant_leaf', 'is_lychee_leaf', 'lychee_confidence', 'subject', 'leaf_surface', 'quality_ok', 'quality_issues', 'observed_symptoms', 'reasoning', 'scores', 'primary', 'affected_area_percent', 'lesions', 'retake_advice']
};

// ---------------------------------------------------------------------------
// Tiện ích
// ---------------------------------------------------------------------------
const RATE_WINDOW_MS = 60_000;
const RATE_MAX = 8;
const hits = new Map();
function rateLimited(ip) {
  const now = Date.now();
  const list = (hits.get(ip) || []).filter((t) => now - t < RATE_WINDOW_MS);
  list.push(now);
  hits.set(ip, list);
  if (hits.size > 500) hits.clear();
  return list.length > RATE_MAX;
}

function readBody(req) {
  if (req.body && typeof req.body === 'object') return Promise.resolve(req.body);
  if (typeof req.body === 'string') {
    try { return Promise.resolve(JSON.parse(req.body)); } catch { return Promise.resolve({}); }
  }
  return new Promise((resolve) => {
    let raw = '';
    req.on('data', (c) => { raw += c; if (raw.length > 12_000_000) req.destroy(); });
    req.on('end', () => { try { resolve(JSON.parse(raw || '{}')); } catch { resolve({}); } });
    req.on('error', () => resolve({}));
  });
}

function parseDataUrl(s) {
  const m = /^data:(image\/(?:jpeg|jpg|png|webp|heic|heif));base64,([A-Za-z0-9+/=\s]+)$/i.exec(String(s || ''));
  if (!m) return null;
  const data = m[2].replace(/\s/g, '');
  const bytes = Math.floor((data.length * 3) / 4);
  if (bytes < 1_000 || bytes > MAX_IMAGE_BYTES) return null;
  return { mimeType: m[1].toLowerCase().replace('jpg', 'jpeg'), data };
}

const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, Number.isFinite(n) ? n : lo));

/** Chuẩn hoá điểm về tổng 100 (giữ 1 chữ số thập phân) */
function normalizeScores(raw) {
  const s = Object.fromEntries(CLASSES.map((c) => [c, clamp(Number(raw?.[c]), 0, 100)]));
  const total = CLASSES.reduce((a, c) => a + s[c], 0);
  if (total <= 0) return Object.fromEntries(CLASSES.map((c) => [c, c === 'Other' ? 100 : 0]));
  return Object.fromEntries(CLASSES.map((c) => [c, Math.round((s[c] / total) * 1000) / 10]));
}

/** Gộp nhiều lượt phân tích (self-consistency): trung bình điểm, bỏ phiếu cho các trường bool */
function mergeVotes(votes) {
  if (votes.length === 1) return votes[0];
  const avg = (f) => votes.reduce((a, v) => a + Number(f(v) || 0), 0) / votes.length;
  const majority = (f) => votes.filter(f).length * 2 >= votes.length;
  const scores = Object.fromEntries(CLASSES.map((c) => [c, avg((v) => v.scores?.[c])]));
  const best = votes.reduce((a, v) => ((v.scores?.[v.primary] || 0) > (a.scores?.[a.primary] || 0) ? v : a), votes[0]);
  return {
    ...best,
    is_plant_leaf: majority((v) => v.is_plant_leaf),
    is_lychee_leaf: majority((v) => v.is_lychee_leaf),
    lychee_confidence: Math.round(avg((v) => v.lychee_confidence)),
    quality_ok: majority((v) => v.quality_ok),
    quality_issues: [...new Set(votes.flatMap((v) => v.quality_issues || []))],
    affected_area_percent: Math.round(avg((v) => v.affected_area_percent)),
    scores
  };
}

function severityFromArea(area) {
  if (area >= 30) return 'Nghiêm trọng';
  if (area >= 10) return 'Trung bình';
  return 'Nhẹ';
}

function buildResult(raw, meta) {
  const scores = normalizeScores(raw.scores);
  const ranked = CLASSES.map((c) => [c, scores[c]]).sort((a, b) => b[1] - a[1]);
  const [topClass, topScore] = ranked[0];
  const margin = topScore - (ranked[1]?.[1] || 0);
  const area = clamp(Math.round(Number(raw.affected_area_percent)), 0, 100);
  const lycheeConf = clamp(Math.round(Number(raw.lychee_confidence)), 0, 100);
  const issues = (raw.quality_issues || []).filter((q) => QUALITY_ISSUES.includes(q));

  // Phán quyết cuối: ưu tiên an toàn, không ép ra tên bệnh khi bằng chứng yếu
  let verdict = 'diagnosed';
  if (!raw.is_plant_leaf || (!raw.is_lychee_leaf && lycheeConf < 40)) verdict = 'not_lychee';
  else if (topClass === 'Other') verdict = 'other';
  else if (topClass === 'Healthy') verdict = topScore >= 60 ? 'healthy' : 'uncertain';
  else if (topScore < 50 || margin < 12) verdict = 'uncertain';
  if (verdict !== 'not_lychee' && !raw.quality_ok && topScore < 70) verdict = 'retake';

  const lesions = (Array.isArray(raw.lesions) ? raw.lesions : [])
    .filter((l) => Array.isArray(l.box_2d) && l.box_2d.length === 4 && CLASSES.includes(l.label) && l.label !== 'Healthy')
    .slice(0, 8)
    .map((l) => {
      const [ymin, xmin, ymax, xmax] = l.box_2d.map((v) => clamp(Number(v), 0, 1000) / 1000);
      return { label: l.label, box: [Math.min(ymin, ymax), Math.min(xmin, xmax), Math.max(ymin, ymax), Math.max(xmin, xmax)] };
    })
    .filter((l) => l.box[2] - l.box[0] > 0.01 && l.box[3] - l.box[1] > 0.01);

  return {
    success: true,
    engine: 'gemini-vision',
    model: meta.model,
    votes: meta.votes,
    latency_ms: meta.latency,
    verdict,
    image_check: {
      is_plant_leaf: Boolean(raw.is_plant_leaf),
      is_lychee_leaf: Boolean(raw.is_lychee_leaf),
      lychee_confidence: lycheeConf,
      subject: String(raw.subject || '').slice(0, 200),
      leaf_surface: raw.leaf_surface || 'unknown',
      quality_ok: Boolean(raw.quality_ok),
      quality_issues: issues
    },
    scores,
    ranked: ranked.map(([cls, p]) => ({ class: cls, probability: p })),
    primary: topClass,
    confidence: topScore,
    margin: Math.round(margin * 10) / 10,
    affected_area_percent: area,
    severity: topClass === 'Healthy' || topClass === 'Other' ? null : severityFromArea(area),
    observed_symptoms: (raw.observed_symptoms || []).map((s) => String(s).slice(0, 200)).slice(0, 6),
    reasoning: String(raw.reasoning || '').slice(0, 800),
    lesions,
    retake_advice: String(raw.retake_advice || '').slice(0, 300)
  };
}

// ---------------------------------------------------------------------------
// Gọi Gemini
// ---------------------------------------------------------------------------
async function callGemini({ apiKey, model, parts, temperature, signal }) {
  const isPro = model.includes('pro');
  const res = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'x-goog-api-key': apiKey },
      signal,
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: SYSTEM_PROMPT }] },
        contents: [{ role: 'user', parts }],
        generationConfig: {
          temperature,
          responseMimeType: 'application/json',
          responseSchema: RESPONSE_SCHEMA,
          maxOutputTokens: 8192,
          // Cho mô hình "suy nghĩ" có giới hạn: tăng độ chính xác phân biệt bệnh dễ nhầm
          ...(model.includes('2.5') ? { thinkingConfig: { thinkingBudget: isPro ? 2048 : 1024 } } : {})
        }
      })
    }
  );
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(`Gemini ${res.status}: ${data?.error?.message || 'error'}`);
    err.status = res.status;
    throw err;
  }
  const text = (data.candidates?.[0]?.content?.parts || []).filter((p) => !p.thought).map((p) => p.text || '').join('');
  try {
    return JSON.parse(text);
  } catch {
    const err = new Error(`Gemini trả JSON không hợp lệ (finish: ${data.candidates?.[0]?.finishReason})`);
    err.status = 502;
    throw err;
  }
}

module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (req.method === 'OPTIONS') return res.status(204).end();
  if (req.method !== 'POST') return res.status(405).json({ success: false, error: 'Method not allowed' });

  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) return res.status(503).json({ success: false, error: 'GEMINI_API_KEY chưa được cấu hình' });

  const ip = String(req.headers['x-forwarded-for'] || req.socket?.remoteAddress || 'unknown').split(',')[0].trim();
  if (rateLimited(ip)) return res.status(429).json({ success: false, error: 'Bạn quét quá nhanh, vui lòng chờ một phút rồi thử lại.' });

  const body = await readBody(req);
  const rawImages = Array.isArray(body.images) ? body.images : body.image ? [body.image] : [];
  const images = rawImages.slice(0, MAX_IMAGES).map(parseDataUrl).filter(Boolean);
  if (!images.length) {
    return res.status(400).json({ success: false, error: 'Ảnh không hợp lệ (cần JPEG/PNG/WebP dạng data URL, tối đa 3 MB mỗi ảnh).' });
  }

  const ctx = body.context || {};
  const surfaceHint = { top: 'mặt trên lá', bottom: 'mặt dưới lá', both: 'cả hai mặt lá' }[ctx.surface] || '';
  const userText = [
    `Phân tích ${images.length > 1 ? `${images.length} ảnh của CÙNG MỘT lá/cành vải` : 'ảnh lá'} sau.`,
    surfaceHint ? `Người dùng cho biết ảnh chụp ${surfaceHint}.` : '',
    ctx.note ? `Ghi chú của nông dân: ${String(ctx.note).slice(0, 300)}` : '',
    'Trả về JSON đúng schema.'
  ].filter(Boolean).join(' ');

  const parts = [
    ...images.map((img) => ({ inlineData: { mimeType: img.mimeType, data: img.data } })),
    { text: userText }
  ];

  const primaryModel = process.env.GEMINI_VISION_MODEL || 'gemini-2.5-flash';
  const fallbackModel = process.env.GEMINI_VISION_FALLBACK || 'gemini-2.5-flash-lite';
  const votes = clamp(parseInt(process.env.DIAGNOSE_VOTES || '1', 10), 1, 3);

  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), UPSTREAM_TIMEOUT_MS);
  const t0 = Date.now();

  const runWith = async (model) => {
    const temps = [0, 0.3, 0.6].slice(0, votes);
    const settled = await Promise.allSettled(temps.map((t) => callGemini({ apiKey, model, parts, temperature: t, signal: ctrl.signal })));
    const ok = settled.filter((s) => s.status === 'fulfilled').map((s) => s.value);
    if (!ok.length) throw settled[0].reason;
    return { raw: mergeVotes(ok), count: ok.length, model };
  };

  try {
    let out;
    try {
      out = await runWith(primaryModel);
    } catch (err) {
      // Quá tải / hết quota tạm thời → thử model dự phòng
      if (fallbackModel && fallbackModel !== primaryModel && [429, 500, 503].includes(err.status)) {
        console.warn('[diagnose] primary model failed, fallback:', err.message);
        out = await runWith(fallbackModel);
      } else {
        throw err;
      }
    }
    return res.status(200).json(buildResult(out.raw, { model: out.model, votes: out.count, latency: Date.now() - t0 }));
  } catch (err) {
    const timeout = err?.name === 'AbortError';
    console.error('[diagnose] failed', timeout ? 'timeout' : err?.message);
    const status = timeout ? 504 : err.status === 429 ? 429 : 502;
    return res.status(status).json({
      success: false,
      error: status === 429 ? 'Dịch vụ AI đang quá tải, vui lòng thử lại sau ít phút.' : timeout ? 'AI phản hồi quá lâu, vui lòng thử lại.' : 'Không phân tích được ảnh lúc này.'
    });
  } finally {
    clearTimeout(timer);
  }
};

// Xuất để kiểm thử đơn vị
module.exports._internal = { buildResult, normalizeScores, mergeVotes, parseDataUrl, RESPONSE_SCHEMA };

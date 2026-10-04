/**
 * LEAF_AI — API Service Client
 * Kết nối REST API Django backend. Nếu backend không chạy, tự chuyển sang
 * chế độ mô phỏng phía trình duyệt (kết quả được gắn cờ `simulated: true`).
 */
class LeafApiService {
  constructor(baseUrl = 'http://127.0.0.1:8000') {
    let customUrl = null;
    try { customUrl = localStorage.getItem('leaf_backend_url'); } catch { /* private mode */ }
    const isLocalhost = ['localhost', '127.0.0.1', ''].includes(window.location.hostname);
    if (customUrl) {
      this.baseUrl = customUrl;
    } else if (!isLocalhost || window.location.protocol === 'https:') {
      this.baseUrl = ''; // On Vercel / Cloud deployment, use relative paths to same origin
    } else {
      this.baseUrl = window.location.port === '8000' ? '' : baseUrl;
    }
    this._online = null; // Promise<boolean>, kiểm tra 1 lần cho mỗi trang
  }

  /** fetch có timeout và credentials để quản lý phiên đăng nhập */
  async _fetch(path, options = {}, timeoutMs = 8000) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
      return await fetch(`${this.baseUrl}${path}`, {
        credentials: 'include',
        ...options,
        signal: ctrl.signal
      });
    } finally {
      clearTimeout(timer);
    }
  }

  /** Backend có sẵn sàng không (ghi nhớ kết quả) */
  isOnline() {
    if (!this._online) {
      this._online = this._fetch('/health/', { method: 'GET' }, 2500)
        .then((r) => r.ok)
        .catch(() => false);
    }
    return this._online;
  }

  async _getJson(path, timeoutMs) {
    if (!(await this.isOnline())) return null;
    try {
      const res = await this._fetch(path, {}, timeoutMs);
      return res.ok ? await res.json() : null;
    } catch {
      return null;
    }
  }

  async getDiseases(category = '', query = '') {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (query) params.append('q', query);
    const json = await this._getJson(`/api/diseases/?${params}`);
    return json?.data || Object.values(LEAF_DATA.diseases);
  }

  async getHandbook(section = '') {
    const json = await this._getJson(section ? `/api/handbook/?section=${section}` : '/api/handbook/');
    return json?.data || LEAF_DATA.handbook;
  }

  async getStats() {
    const json = await this._getJson('/api/stats/');
    return json?.data || null;
  }

  /**
   * Chuẩn hoá nguồn ảnh trước khi gửi: ảnh mẫu (đường dẫn) -> data URL
   * để backend nhận đủ bytes; data URL / File / Blob giữ nguyên.
   */
  async _toDataUrl(image) {
    if (typeof image !== 'string' || image.startsWith('data:')) return image;
    try {
      const res = await fetch(image);
      if (!res.ok) return image;
      const blob = await res.blob();
      return await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });
    } catch {
      return image; // để backend tự xử lý (400) và FE chuyển sang mô phỏng
    }
  }

  async diagnose(image, modelVersion = 'v3', confidence = 0.25) {
    // Ảnh mẫu trong thư mục assets/samples là hình minh họa vẽ tay: không gửi lên máy chủ
    if (typeof image === 'string' && /assets\/samples\/sample_/.test(image)) {
      await new Promise((r) => setTimeout(r, 350));
      return this.simulateDetection(modelVersion, image);
    }
    const payload = await this._toDataUrl(image);

    // Ưu tiên 1: Kết nối trực tiếp máy chủ AI Render (ResNet-18 Deep Learning + Grad-CAM)
    const aiEngineUrl = this.engineUrl();

    if (aiEngineUrl) {
      try {
        const res = await fetch(`${aiEngineUrl}/predict_with_gradcam`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            data: payload,
            model_version: modelVersion,
            confidence: confidence
          })
        });
        if (res.ok) {
          const aiData = await res.json();
          return this._formatAiEngineResult(aiData, modelVersion);
        }
      } catch (err) {
        console.warn('[LEAF_AI] Không thể kết nối AI Engine trực tiếp trên Render, thử qua backend proxy:', err);
      }
    }

    // Ưu tiên 2: Kết nối qua Backend Django / FastAPI
    if (await this.isOnline()) {
      try {
        const formData = new FormData();
        formData.append('image', payload);
        formData.append('model_version', modelVersion);
        formData.append('confidence', confidence);
        const res = await this._fetch('/api/diagnose/', { method: 'POST', body: formData }, 60000);
        if (res.ok) return this._checkLycheeLabels(await res.json());
        if (res.status === 429) {
          const j = await res.json().catch(() => ({}));
          throw Object.assign(new Error(j.error || 'Bạn quét quá nhanh, vui lòng chờ một phút rồi thử lại.'), { code: 429 });
        }
      } catch (e) {
        if (e.code === 429) throw e;
        console.warn('[LEAF_AI] Backend lỗi, chuyển sang mô phỏng:', e);
      }
    }
    // Giữ nhịp như suy luận thật để hiệu ứng quét không bị giật
    await new Promise((r) => setTimeout(r, 350));
    return this.simulateDetection(modelVersion, image);
  }

  /** Địa chỉ máy chủ AI trên Render (đổi được qua localStorage 'leaf_ai_engine_url') */
  engineUrl() {
    let url = 'https://leaf-ai-engine.onrender.com';
    try {
      const custom = localStorage.getItem('leaf_ai_engine_url');
      if (custom) url = custom;
    } catch { /* private mode */ }
    return url.replace(/\/+$/, '');
  }

  /**
   * Lập phác đồ điều trị sau chẩn đoán.
   * Gọi POST /treatment/plan trên máy chủ AI; máy chủ đang khởi động hoặc mất mạng
   * thì lập bằng bộ lập phác đồ trong trình duyệt (cùng thuật toán, cùng kho tri thức).
   */
  async getTreatmentPlan(opts, timeoutMs = 15000) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
      const res = await fetch(`${this.engineUrl()}/treatment/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(opts),
        signal: ctrl.signal
      });
      if (res.ok) return await res.json();
      if (res.status === 422) {
        const j = await res.json().catch(() => ({}));
        if (typeof j.detail === 'string') throw Object.assign(new Error(j.detail), { code: 422 });
      }
    } catch (err) {
      if (err.code === 422) throw err;
      console.warn('[LEAF_AI] Máy chủ phác đồ chưa sẵn sàng, lập phác đồ trên máy:', err);
    } finally {
      clearTimeout(timer);
    }
    const kb = await window.LeafTreatment.loadKB();
    return window.LeafTreatment.build(kb, opts);
  }

  /** Tra thông tin bệnh lá vải theo tên lớp mô hình trả về (có xử lý tên gọi khác) */
  _lookup(cls) {
    if (window.Leaf && window.Leaf.diseases) return window.Leaf.diseases.find(cls);
    const k = String(cls || '').toLowerCase();
    return Object.values(LEAF_DATA.diseases).find((d) => d.id === k || (d.aliases || []).includes(k)) || null;
  }

  _isHealthy(cls) {
    if (window.Leaf && window.Leaf.diseases) return window.Leaf.diseases.isHealthy(cls);
    return String(cls || '').toLowerCase() === 'healthy';
  }

  /** Kết quả không chứa nhãn lá vải (máy chủ còn chạy mô hình cũ) thì không hiển thị như một chẩn đoán */
  _unsupportedResult(labels, modelVersion) {
    return {
      success: true,
      id: Date.now(),
      model_version: modelVersion,
      analysis_unavailable: true,
      unsupported: true,
      healthy: false,
      primary_disease: null,
      secondary_diseases: [],
      detections: [],
      lesion_count: 0,
      note: `Máy chủ AI trả về nhãn chưa thuộc danh mục bệnh lá vải (${labels.join(', ')}). Cần cập nhật mô hình lá vải lên máy chủ trước khi dùng kết quả này.`
    };
  }

  _checkLycheeLabels(result) {
    const p = result && result.primary_disease;
    if (!p || this._isHealthy(p.class) || this._lookup(p.class)) return result;
    return this._unsupportedResult([p.class], result.model_version || 'v3');
  }

  /** Chuẩn hóa kết quả trả về từ máy chủ AI (ResNet-18 + Grad-CAM) */
  _formatAiEngineResult(aiData, modelVersion) {
    const all = aiData.results || [];
    const heatmap = aiData.heatmap_base64
      ? (aiData.heatmap_base64.startsWith('data:') ? aiData.heatmap_base64 : `data:image/jpeg;base64,${aiData.heatmap_base64}`)
      : null;
    const top = all[0] || null;
    if (top && !this._isHealthy(top.class) && !this._lookup(top.class)) {
      return this._unsupportedResult(all.map((r) => r.class), modelVersion);
    }
    const healthy = !top || this._isHealthy(top.class);
    const sev = (p) => (p >= 60 ? 'Nghiêm trọng' : p >= 35 ? 'Trung bình' : 'Nhẹ');
    const toDisease = (r) => {
      const d = this._lookup(r.class) || {};
      return {
        class: r.class,
        id: d.id,
        name_en: d.name_en || r.class,
        name_vi: d.name_vi || r.name_vi || r.class,
        probability: r.probability,
        severity: sev(r.probability),
        color: d.color || '#d4452a',
        treatment: d.treatment || {}
      };
    };

    const primaryDisease = healthy ? null : toDisease(top);
    // Bệnh phụ: chỉ giữ nhãn lá vải có xác suất đáng kể (quy tắc cảnh báo nghi đồng nhiễm: ≥ 25%)
    const secondaryDiseases = healthy ? [] : all.slice(1)
      .filter((r) => this._lookup(r.class) && r.probability >= 25)
      .map(toDisease);

    let reportHtml = '';
    if (healthy) {
      reportHtml = '<div class="callout callout-info"><strong>Không phát hiện dấu hiệu bệnh hại trên lá vải.</strong><br>Khuyến nghị: tiếp tục thăm vườn 1–2 lần mỗi tuần, chú ý các đợt lộc non và những ngày mưa phùn, nồm ẩm.</div>';
    } else {
      const t = primaryDisease.treatment || {};
      reportHtml = `
        <h3>Kết quả chẩn đoán học sâu và Grad-CAM</h3>
        <p>Bệnh chính: <strong>${primaryDisease.name_vi}</strong> (<em>${primaryDisease.name_en}</em>)<br>
        Độ tin cậy: <span class="pct">${primaryDisease.probability}%</span> — Mức độ: <span class="badge ${primaryDisease.severity === 'Nghiêm trọng' ? 'badge-high' : 'badge-mid'}">${primaryDisease.severity}</span></p>
        <div class="callout callout-info">
          <strong>Giải thích bằng Grad-CAM:</strong> chọn chế độ <em>"Bản đồ nhiệt Grad-CAM"</em> để xem vùng ảnh mà mô hình ResNet-18 dựa vào khi kết luận. Vùng đỏ nên trùng với vết bệnh trên lá.
        </div>
        <h3>Phác đồ quản lý dịch hại tổng hợp (IPM)</h3>
        <table class="report-table">
          <thead><tr><th>Biện pháp</th><th>Hướng dẫn thực hiện</th></tr></thead>
          <tbody>
            <tr><td><strong>1. Canh tác</strong></td><td>${t.cultural || 'Cắt bỏ lá, cành bị bệnh và tiêu hủy xa vườn.'}</td></tr>
            <tr><td><strong>2. Sinh học</strong></td><td>${t.biological || 'Dùng chế phẩm Trichoderma, Bacillus subtilis.'}</td></tr>
            <tr><td><strong>3. Hóa học</strong></td><td>${t.chemical || 'Chỉ dùng thuốc trong danh mục được phép, tuân thủ 4 đúng và thời gian cách ly.'}</td></tr>
          </tbody>
        </table>`;
    }

    return {
      success: true,
      id: Date.now(),
      model_version: modelVersion,
      model_badge: 'ResNet-18',
      healthy,
      is_coinfection: secondaryDiseases.length > 0,
      warning_banner: secondaryDiseases.length > 0 ? 'Nghi đồng nhiễm' : null,
      primary_disease: primaryDisease,
      secondary_diseases: secondaryDiseases,
      heatmap_base64: heatmap,
      // Mô hình phân loại cả ảnh, không khoanh từng vết: vị trí vết bệnh xem trên bản đồ nhiệt
      detections: [],
      lesion_count: healthy ? 0 : null,
      report_html: reportHtml,
      note: ''
    };
  }

  async getHistory(limit = 50) {
    const json = await this._getJson(`/api/history/?limit=${limit}`);
    return json?.data || null; // null = dùng localStorage
  }

  async deleteHistoryRecord(recordId) {
    if (!(await this.isOnline())) return { success: true, local: true };
    try {
      const res = await this._fetch(`/api/history/${recordId}/delete/`, { method: 'DELETE' });
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn('[LEAF_AI] Xóa trên backend lỗi:', e);
    }
    return { success: true, local: true };
  }

  async clearHistoryAll() {
    if (!(await this.isOnline())) return { success: true, local: true };
    try {
      const res = await this._fetch('/api/history/clear/', { method: 'DELETE' });
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn('[LEAF_AI] Xóa toàn bộ trên backend lỗi:', e);
    }
    return { success: true, local: true };
  }

  async getSupabaseStatus() {
    const json = await this._getJson('/api/supabase/status/');
    return json?.status || { configured: false, connected: false };
  }

  async sendChatMessage(message) {
    if (await this.isOnline()) {
      try {
        const res = await this._fetch('/api/chat/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message })
        }, 45000);
        if (res.ok) return await res.json();
        if (res.status === 429) return { reply: 'Bạn gửi hơi nhanh. Đợi khoảng một phút rồi hỏi tiếp nhé.' };
      } catch (err) {
        console.warn('[LEAF_AI] Chatbot API lỗi, dùng trả lời ngoại tuyến:', err);
      }
    }
    return { reply_html: this.offlineAnswer(message), offline: true };
  }

  // ==========================================================================
  // Xác thực người dùng (Auth REST API)
  // ==========================================================================

  async getCurrentUser() {
    if (!(await this.isOnline())) return { success: true, authenticated: false, user: null };
    try {
      const res = await this._fetch('/api/auth/user/', { method: 'GET' }, 3500);
      return res.ok ? await res.json() : { success: false, authenticated: false, user: null };
    } catch {
      return { success: false, authenticated: false, user: null };
    }
  }

  async login(username, password) {
    if (!(await this.isOnline())) {
      throw new Error('Máy chủ đang ngoại tuyến. Vui lòng thử lại sau.');
    }
    const res = await this._fetch('/api/auth/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    }, 10000);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || 'Đăng nhập không thành công.');
    return data;
  }

  async signup(username, email, password, birthDate = '') {
    if (!(await this.isOnline())) {
      throw new Error('Máy chủ đang ngoại tuyến. Vui lòng thử lại sau.');
    }
    const res = await this._fetch('/api/auth/signup/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, email, password, birth_date: birthDate })
    }, 10000);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || 'Đăng ký không thành công.');
    return data;
  }

  async logout() {
    if (await this.isOnline()) {
      try {
        await this._fetch('/api/auth/logout/', { method: 'POST' }, 5000);
      } catch (e) {
        console.warn('[LEAF_AI] Lỗi khi đăng xuất:', e);
      }
    }
    return { success: true };
  }

  // ==========================================================================
  // Chế độ ngoại tuyến
  // ==========================================================================

  /** Trả lời từ kho tri thức cục bộ khi không có backend */
  offlineAnswer(message) {
    const q = String(message || '').toLowerCase();
    const esc = (s) => String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
    const keywords = {
      erinose: ['lông nhung', 'nhện', 'aceria', 'erinose', 'lông tơ', 'phồng rộp'],
      downy_blight: ['sương mai', 'mốc trắng', 'peronophythora', 'downy', 'thối quả'],
      anthracnose: ['thán thư', 'colletotrichum', 'anthracnose', 'chấm đen xếp vòng'],
      algal_spot: ['đốm rong', 'rong', 'tảo', 'đỏ gạch', 'cephaleuros', 'rỉ sắt'],
      leaf_blight: ['cháy lá', 'cháy chóp', 'cháy mép', 'pestalotiopsis', 'khô chóp']
    };
    const hit = Object.entries(keywords).find(([, words]) => words.some((w) => q.includes(w)));
    if (hit) {
      const d = Object.values(LEAF_DATA.diseases).find((x) => x.id === hit[0]);
      return `<p><strong>${esc(d.name_vi)}</strong> (<em>${esc(d.pathogen)}</em>)</p>
        <p>Dấu hiệu sớm: ${esc(d.symptoms.stage_1)}</p>
        <ul>
          <li><strong>Canh tác:</strong> ${esc(d.treatment.cultural)}</li>
          <li><strong>Sinh học:</strong> ${esc(d.treatment.biological)}</li>
          <li><strong>Hóa học (khi cần):</strong> ${esc(d.treatment.chemical)}</li>
        </ul>
        <p><a href="disease.html?id=${d.id}">Xem đầy đủ phác đồ ${esc(d.name_vi)}</a></p>`;
    }
    if (/(phi|cách ly|thu hoạch)/.test(q)) {
      return '<p>Ngừng phun thuốc BVTV trước thu hoạch <strong>đúng số ngày ghi trên nhãn</strong> của từng loại thuốc. Với vải xuất khẩu, cần kiểm tra thêm danh mục hoạt chất và mức dư lượng (MRL) mà nước nhập khẩu cho phép.</p><p><a href="handbook.html#an-toan">Xem quy tắc an toàn BVTV</a></p>';
    }
    if (/(trichoderma|ủ phân|vi sinh|hữu cơ)/.test(q)) {
      return '<p>Trộn chế phẩm <strong>Trichoderma</strong> với phân chuồng hoai mục, giữ ẩm 50–60%, đậy bạt và đảo sau 7–10 ngày. Bón quanh hình chiếu tán vải sau thu hoạch, lấp một lớp đất mỏng để nấm đối kháng phát triển trong vùng rễ.</p>';
    }
    if (/(lộc|tỉa|cắt cành|sau thu hoạch)/.test(q)) {
      return '<p>Sau thu hoạch, tỉa bỏ cành tăm, cành sâu bệnh và cành bị nhện lông nhung để tán thông thoáng. Nuôi các đợt lộc thu ra đồng loạt, kiểm tra kỹ khi lộc dài 3–5 cm vì đây là lúc nhện lông nhung và thán thư dễ tấn công.</p><p><a href="handbook.html#nguyen-tac">Xem 8 nguyên tắc canh tác</a></p>';
    }
    if (/(ipm|tổng hợp|fao)/.test(q)) {
      return '<p>IPM ưu tiên theo thứ tự: cây giống khỏe, thăm đồng 2 lần/tuần, bảo vệ thiên địch, biện pháp canh tác và sinh học. Thuốc hóa học chỉ dùng khi dịch vượt ngưỡng kinh tế.</p><p><a href="handbook.html#ipm">Xem 10 bước IPM</a></p>';
    }
    return '<p>Hiện chưa kết nối được máy chủ trợ lý nên mình trả lời từ kho kiến thức có sẵn. Hãy mô tả rõ hơn: màu vết bệnh, vị trí trên lá (chóp, mép, mặt trên hay mặt dưới), lộc non hay lá già, thời tiết mấy ngày qua.</p><p>Hoặc <a href="scan.html">chụp ảnh lá để AI khoanh vùng</a>.</p>';
  }

  /**
   * Kết quả mô phỏng cho ảnh mẫu minh họa (không gọi máy chủ AI).
   * Toạ độ khung lấy từ đúng vị trí vết bệnh vẽ trên ảnh mẫu (800×600).
   */
  simulateDetection(modelVersion, image) {
    const src = typeof image === 'string' ? image : '';
    const sampleKey = (src.match(/sample_([a-z_]+)\.jpg/) || [])[1] || 'upload';

    const PROFILES = {
      anthracnose: { main: ['Anthracnose', 91], second: ['Leaf_blight', 6], boxes: [[337, 491, 101, 101], [337, 214, 84, 84], [459, 369, 84, 84], [461, 12, 106, 106], [558, 193, 84, 84]] },
      downy_blight: { main: ['Downy_blight', 88], second: ['Anthracnose', 9], boxes: [[311, 193, 105, 105], [458, 86, 115, 115], [610, 203, 95, 95]] },
      leaf_blight: { main: ['Leaf_blight', 62], second: ['Anthracnose', 31], boxes: [[180, 304, 67, 84], [482, 352, 112, 82], [649, 217, 85, 72]] },
      algal_spot: { main: ['Algal_spot', 94], second: null, boxes: [[273, 483, 91, 80], [317, 200, 77, 93], [471, 117, 80, 97], [592, 219, 94, 79]] },
      erinose: { main: ['Erinose', 90], second: null, boxes: [[177, 349, 92, 92], [302, 215, 106, 106], [456, 356, 92, 92], [552, 199, 110, 110]] },
      healthy: null
    };

    const base = { success: true, simulated: true, sample: sampleKey !== 'upload', id: Date.now(), model_version: modelVersion };
    const profile = PROFILES[sampleKey];
    if (!profile) {
      return { ...base, healthy: true, primary_disease: null, secondary_diseases: [], detections: [], lesion_count: 0, is_coinfection: false };
    }

    const sev = (p) => (p >= 60 ? 'Nghiêm trọng' : p >= 35 ? 'Trung bình' : 'Nhẹ');
    const make = ([cls, p]) => {
      const d = this._lookup(cls) || {};
      return { class: cls, id: d.id, name_en: d.name_en, name_vi: d.name_vi, probability: p, severity: sev(p), color: d.color, treatment: d.treatment };
    };
    const primary = make(profile.main);
    const secondary = profile.second && profile.second[1] >= 25 ? [make(profile.second)] : [];
    const detections = profile.boxes.map((bbox, i) => ({
      class: primary.class,
      name_vi: primary.name_vi,
      confidence: (primary.probability - i * 4) / 100,
      probability_percent: primary.probability - i * 4,
      color: primary.color,
      bbox
    }));

    return {
      ...base,
      healthy: false,
      note: '',
      lesion_count: detections.length,
      is_coinfection: secondary.length > 0,
      primary_disease: primary,
      secondary_diseases: secondary,
      heatmap_url: `assets/samples/cam_${sampleKey}.jpg`,
      detections
    };
  }
}

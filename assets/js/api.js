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

  async diagnose(image, modelVersion = 'v3', confidence = 0.25) {
    if (await this.isOnline()) {
      try {
        const formData = new FormData();
        formData.append('image', image);
        formData.append('model_version', modelVersion);
        formData.append('confidence', confidence);
        const res = await this._fetch('/api/diagnose/', { method: 'POST', body: formData }, 60000);
        if (res.ok) return await res.json();
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
      early_blight: ['úa sớm', 'đốm vòng', 'alternaria', 'early', 'đồng tâm'],
      late_blight: ['sương mai', 'mốc sương', 'phytophthora', 'late'],
      bacterial_spot: ['vi khuẩn', 'xanthomonas', 'bacterial', 'kasugamycin', 'gốc đồng'],
      septoria_leaf_spot: ['septoria', 'đốm lá nhỏ', 'chấm đen'],
      leaf_mold: ['mốc lá', 'nấm mốc', 'nhà kính', 'passalora'],
      powdery_mildew: ['phấn trắng', 'bột trắng', 'mildew', 'neem']
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
      return '<p>Ngừng phun thuốc BVTV trước thu hoạch đúng số ngày ghi trên nhãn, với cà chua thường là <strong>7–14 ngày</strong>. Hết thời gian cách ly mới hái quả để không tồn dư hoạt chất.</p><p><a href="handbook.html#an-toan">Xem quy tắc an toàn BVTV</a></p>';
    }
    if (/(trichoderma|ủ phân|vi sinh|hữu cơ)/.test(q)) {
      return '<p>Trộn chế phẩm <strong>Trichoderma</strong> với phân chuồng hoai mục, giữ ẩm 50–60%, đậy bạt và đảo sau 7–10 ngày. Bón lót vào hốc trước khi trồng để nấm đối kháng chiếm chỗ của nấm gây bệnh vùng rễ.</p>';
    }
    if (/(ipm|tổng hợp|fao)/.test(q)) {
      return '<p>IPM ưu tiên theo thứ tự: cây giống khỏe, thăm đồng 2 lần/tuần, bảo vệ thiên địch, biện pháp canh tác và sinh học. Thuốc hóa học chỉ dùng khi dịch vượt ngưỡng kinh tế.</p><p><a href="handbook.html#ipm">Xem 10 bước IPM</a></p>';
    }
    return '<p>Hiện chưa kết nối được máy chủ trợ lý nên mình trả lời từ kho kiến thức có sẵn. Hãy mô tả rõ hơn: màu vết bệnh, vị trí trên lá (mặt trên hay mặt dưới), lá già hay lá non, thời tiết mấy ngày qua.</p><p>Hoặc <a href="scan.html">chụp ảnh lá để AI khoanh vùng</a>.</p>';
  }

  /**
   * Mô phỏng YOLOv8 khi chưa có backend.
   * Với ảnh mẫu, dùng toạ độ vết bệnh thật trên ảnh (800×600) để demo sát thực tế.
   */
  simulateDetection(modelVersion, image) {
    const V3_CLASSES = ['Bacterial_spot', 'Early_blight', 'Late_blight'];
    const src = typeof image === 'string' ? image : '';
    const sampleKey = (src.match(/sample_([a-z_]+)\.jpg/) || [])[1] || 'upload';

    const PROFILES = {
      early_blight: [
        ['Early_blight', 91, [565, 30, 112, 112]],
        ['Early_blight', 87, [394, 124, 92, 92]],
        ['Early_blight', 78, [528, 228, 84, 84]],
        ['Early_blight', 74, [286, 256, 78, 78]]
      ],
      bacterial_spot: [
        ['Bacterial_spot', 89, [402, 118, 102, 100]],
        ['Bacterial_spot', 84, [570, 26, 104, 128]],
        ['Bacterial_spot', 81, [506, 196, 108, 124]],
        ['Bacterial_spot', 76, [278, 228, 96, 124]]
      ],
      late_blight: [
        ['Late_blight', 93, [556, 36, 118, 108]],
        ['Late_blight', 86, [404, 124, 82, 90]],
        ['Late_blight', 82, [524, 226, 92, 96]]
      ],
      septoria: [
        ['Septoria_leaf_spot', 85, [572, 30, 100, 116]],
        ['Septoria_leaf_spot', 80, [408, 98, 88, 104]],
        ['Septoria_leaf_spot', 77, [506, 198, 102, 120]],
        ['Septoria_leaf_spot', 71, [280, 248, 92, 100]],
        ['Early_blight', 34, [404, 98, 92, 108]]
      ],
      healthy_leaf: [],
      upload: [
        ['Early_blight', 65, [220, 160, 200, 180]],
        ['Bacterial_spot', 42, [80, 80, 150, 130]],
        ['Septoria_leaf_spot', 31, [120, 260, 140, 120]]
      ]
    };

    const all = PROFILES[sampleKey] || PROFILES.upload;
    const usable = modelVersion === 'v4' ? all : all.filter(([cls]) => V3_CLASSES.includes(cls));
    const info = (cls) => Object.values(LEAF_DATA.diseases).find((d) => d.id === cls.toLowerCase()) || {};
    const sev = (p) => (p >= 60 ? 'Nghiêm trọng' : p >= 35 ? 'Trung bình' : 'Nhẹ');

    const detections = usable.map(([cls, p, bbox]) => ({
      class: cls,
      name_vi: info(cls).name_vi || cls,
      confidence: p / 100,
      probability_percent: p,
      color: info(cls).color || '#d4452a',
      bbox
    }));

    // Gom theo bệnh, lấy độ tin cậy cao nhất của mỗi bệnh
    const byClass = {};
    detections.forEach((d) => {
      if (!byClass[d.class] || byClass[d.class].probability < d.probability_percent) {
        const i = info(d.class);
        byClass[d.class] = { class: d.class, name_en: i.name_en, name_vi: i.name_vi, probability: d.probability_percent, severity: sev(d.probability_percent), color: i.color, treatment: i.treatment };
      }
    });
    const ranked = Object.values(byClass).sort((a, b) => b.probability - a.probability);
    const missedByV3 = modelVersion !== 'v4' && all.some(([cls]) => !V3_CLASSES.includes(cls));

    return {
      success: true,
      simulated: true,
      id: Date.now(),
      model_version: modelVersion,
      healthy: ranked.length === 0,
      note: missedByV3 ? 'Vết bệnh trên lá có thể thuộc loại V3 chưa hỗ trợ. Hãy quét lại bằng mô hình V4 để kiểm tra Septoria, mốc lá và phấn trắng.' : '',
      lesion_count: detections.length,
      is_coinfection: ranked.length > 1,
      primary_disease: ranked[0] || null,
      secondary_diseases: ranked.slice(1),
      detections
    };
  }
}

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
    // Gộp signal bên ngoài (người dùng huỷ) với signal timeout
    const { signal: outer, ...rest } = options;
    const onOuterAbort = () => ctrl.abort();
    if (outer) {
      if (outer.aborted) ctrl.abort();
      else outer.addEventListener('abort', onOuterAbort, { once: true });
    }
    try {
      return await fetch(`${this.baseUrl}${path}`, {
        credentials: 'include',
        ...rest,
        signal: ctrl.signal
      });
    } finally {
      clearTimeout(timer);
      if (outer) outer.removeEventListener('abort', onOuterAbort);
    }
  }

  /** Nạp lười kho tri thức disease_data.js cho các trang không include sẵn (index, about) */
  _ensureLeafData() {
    if (typeof LEAF_DATA !== 'undefined') return Promise.resolve(true);
    if (!LeafApiService._leafDataPromise) {
      LeafApiService._leafDataPromise = new Promise((resolve) => {
        const s = document.createElement('script');
        s.src = 'assets/js/disease_data.js';
        s.async = true;
        s.onload = () => resolve(typeof LEAF_DATA !== 'undefined');
        s.onerror = () => { LeafApiService._leafDataPromise = null; resolve(false); };
        document.head.appendChild(s);
      });
    }
    return LeafApiService._leafDataPromise;
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

    const validLycheeIds = ['anthracnose', 'downy_blight', 'leaf_blight', 'algal_spot', 'erinose'];
    let list = null;
    if (Array.isArray(json?.data) && json.data.length > 0) {
      const hasLychee = json.data.some((d) => validLycheeIds.includes(d.id?.toLowerCase()));
      const hasTomato = json.data.some((d) =>
        ['bacterial_spot', 'early_blight', 'late_blight', 'septoria_leaf_spot', 'leaf_mold', 'powdery_mildew'].includes(d.id?.toLowerCase())
      );
      if (hasLychee && !hasTomato) {
        list = json.data;
      }
    }

    if (!list) {
      list = Object.values(LEAF_DATA.diseases);
      if (category === 'fungus') {
        list = list.filter((d) => d.kind === 'Nấm' || d.kind === 'Nấm noãn');
      } else if (category === 'pest') {
        list = list.filter((d) => d.kind === 'Nhện hại');
      } else if (category === 'algae') {
        list = list.filter((d) => d.kind === 'Tảo');
      } else if (category === 'severe') {
        list = list.filter((d) => d.severity_default === 'Nghiêm trọng');
      }
      if (query) {
        const q = query.toLowerCase();
        list = list.filter(
          (d) =>
            (d.name_vi && d.name_vi.toLowerCase().includes(q)) ||
            (d.name_en && d.name_en.toLowerCase().includes(q)) ||
            (d.pathogen && d.pathogen.toLowerCase().includes(q))
        );
      }
    }
    return list;
  }

  async getHandbook(section = '') {
    const json = await this._getJson(section ? `/api/handbook/?section=${section}` : '/api/handbook/');
    if (json?.data && !JSON.stringify(json.data).toLowerCase().includes('cà chua')) {
      return json.data;
    }
    if (section && LEAF_DATA.handbook[section]) {
      return { [section]: LEAF_DATA.handbook[section] };
    }
    return LEAF_DATA.handbook;
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

  /**
   * Chẩn đoán lá vải — chiến lược lai "mô hình trước, Gemini cho ca khó":
   *  1) Mô hình LEAF_AI (CNN huấn luyện trên ảnh lá vải, chạy trên máy chủ Render) — nhanh, có Grad-CAM.
   *  2) Ca khó → hỏi Gemini Vision (/api/diagnose): mô hình chưa chắc chắn (dưới ngưỡng hiệu chỉnh lúc train),
   *     hai lớp sát nhau, nghiêng về "Other", hoặc máy chủ mô hình chưa sẵn sàng/đang khởi động.
   *  3) Kết hợp hai nguồn: đồng thuận → tin cậy cao; bất đồng → báo rõ để người dùng kiểm tra thêm.
   *  Không bao giờ trả kết quả bịa cho ảnh thật: cả hai nguồn lỗi → analysis_unavailable.
   * @param {string} image data URL / đường dẫn ảnh
   * @param {string} modelVersion 'v4' (top-3) | 'v3'
   * @param {{surface?: 'top'|'bottom'|'both', signal?: AbortSignal, onStage?: (stage:string)=>void}} opts
   */
  async diagnose(image, modelVersion = 'v4', opts = {}) {
    // Ảnh mẫu trong assets/samples là hình minh họa vẽ tay: chỉ mô phỏng, không gửi lên AI
    if (typeof image === 'string' && /assets\/samples\/sample_/.test(image)) {
      await new Promise((r) => setTimeout(r, 350));
      return await this.simulateDetection(modelVersion, image);
    }

    const stage = (s) => { try { opts.onStage?.(s); } catch { /* UI callback */ } };
    stage('prepare');
    const prepared = await this._prepareImage(image);

    stage('model');
    const engineP = this._callEngine(prepared.dataUrl, modelVersion, opts.signal);
    // Máy chủ Render gói miễn phí có thể đang ngủ (~1 phút để dậy): sau 7s chưa có kết quả thì hỏi Gemini song song
    const early = await Promise.race([engineP, new Promise((r) => setTimeout(() => r(null), 7000))]);

    let engine;
    let gemini = null;
    if (early === null) {
      stage('second_opinion');
      const geminiP = this._callGemini(prepared.dataUrl, opts);
      gemini = await geminiP;
      engine = await Promise.race([engineP, new Promise((r) => setTimeout(() => r({ ok: false, reason: 'slow' }), 1500))]);
    } else {
      engine = early;
      if (this._needsSecondOpinion(engine)) {
        stage('second_opinion');
        gemini = await this._callGemini(prepared.dataUrl, opts);
      }
    }

    if (gemini && gemini.rateLimited && !(engine.ok && !this._needsSecondOpinion(engine))) {
      throw Object.assign(new Error(gemini.error || 'Bạn quét quá nhanh, vui lòng chờ một phút rồi thử lại.'), { code: 429 });
    }
    stage('done');
    return this._combine(engine, gemini, prepared, modelVersion);
  }

  /** Đánh thức máy chủ mô hình (Render ngủ khi không có truy cập) — gọi khi mở trang quét */
  warmUpEngine() {
    try {
      fetch(`${this.engineUrl()}/health`, { mode: 'cors', cache: 'no-store' }).catch(() => {});
    } catch { /* bỏ qua */ }
  }

  async _prepareImage(image) {
    const src = await this._toDataUrl(image);
    if (typeof window.LeafImage !== 'undefined' && typeof src === 'string') {
      try {
        return await window.LeafImage.prepare(src);
      } catch (err) {
        console.warn('[LEAF_AI] Tiền xử lý ảnh lỗi, gửi ảnh gốc:', err);
      }
    }
    return { dataUrl: src, quality: null };
  }

  _needsSecondOpinion(engine) {
    if (!engine || !engine.ok) return true;
    const d = engine.data;
    return Boolean(d.uncertain) || d.top === 'Other';
  }

  /** Gọi máy chủ mô hình lá vải. Không bao giờ throw: trả {ok, data} hoặc {ok:false, reason} */
  async _callEngine(dataUrl, modelVersion, signal) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 25000);
    const onAbort = () => ctrl.abort();
    signal?.addEventListener('abort', onAbort, { once: true });
    try {
      const res = await fetch(`${this.engineUrl()}/predict_with_gradcam`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data: dataUrl, model_version: modelVersion }),
        signal: ctrl.signal
      });
      if (res.status === 503) return { ok: false, reason: 'not_ready' };
      if (!res.ok) return { ok: false, reason: `http_${res.status}` };
      const data = await res.json();
      // Chỉ chấp nhận máy chủ chạy mô hình LÁ VẢI mới (bản cũ đổi tên lớp từ mô hình cà chua → bỏ qua)
      if (!data || !data.model || data.model.crop !== 'lychee' || !Array.isArray(data.results)) {
        return { ok: false, reason: 'legacy_model' };
      }
      return { ok: true, data };
    } catch (err) {
      return { ok: false, reason: err.name === 'AbortError' ? 'timeout' : 'network' };
    } finally {
      clearTimeout(timer);
      signal?.removeEventListener('abort', onAbort);
    }
  }

  /** Gọi Gemini Vision qua Vercel Function /api/diagnose. Không throw. */
  async _callGemini(dataUrl, opts = {}) {
    if (typeof dataUrl !== 'string' || !dataUrl.startsWith('data:image/')) return null;
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 60000);
    try {
      const res = await fetch('/api/diagnose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ images: [dataUrl], context: { surface: opts.surface || undefined } }),
        signal: ctrl.signal
      });
      const json = await res.json().catch(() => null);
      if (res.status === 429) return { rateLimited: true, error: json?.error };
      if (!res.ok || !json?.success) return null;
      return json;
    } catch (err) {
      console.warn('[LEAF_AI] Gemini Vision lỗi:', err?.name || err);
      return null;
    } finally {
      clearTimeout(timer);
    }
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

  /** Kết quả "chưa phân tích được" — tuyệt đối không giả làm chẩn đoán */
  _unavailableResult(modelVersion, note, extra = {}) {
    return {
      success: true,
      id: Date.now(),
      model_version: modelVersion,
      analysis_unavailable: true,
      healthy: false,
      primary_disease: null,
      secondary_diseases: [],
      detections: [],
      lesion_count: 0,
      note,
      ...extra
    };
  }

  _diseaseEntry(cls, probability, severity) {
    const d = this._lookup(cls) || {};
    return {
      class: cls,
      id: d.id,
      name_en: d.name_en || cls,
      name_vi: d.name_vi || cls,
      probability: Math.round(probability * 10) / 10,
      severity: severity || null,
      color: d.color || '#d4452a',
      treatment: d.treatment || {}
    };
  }

  /**
   * Hợp nhất kết quả mô hình (E) và Gemini (G) thành định dạng trang quét dùng.
   * - Chỉ E và E chắc chắn → nguồn "model".
   * - E chưa chắc + G → trộn xác suất (G 0.6 / E 0.4 vì E đã tự báo chưa chắc), kiểm tra đồng thuận.
   * - E lỗi + G → nguồn "gemini".
   * - G phát hiện ảnh không phải lá vải / ảnh kém → ưu tiên báo người dùng chụp lại.
   */
  _combine(engine, gemini, prepared, modelVersion) {
    const E = engine && engine.ok ? engine.data : null;
    const G = gemini && gemini.success ? gemini : null;
    const quality = prepared?.quality || null;
    const qualityTips = (quality?.issues || []).map((i) => i.message);
    const base = {
      quality,
      quality_tips: qualityTips,
      engine_status: engine?.ok ? 'ok' : (engine?.reason || 'unavailable'),
      model_info: E?.model || null
    };

    if (!E && !G) {
      const why = {
        legacy_model: 'Máy chủ mô hình đang chạy bản cũ (chưa có mô hình lá vải)',
        not_ready: 'Máy chủ mô hình chưa nạp mô hình lá vải',
        timeout: 'Máy chủ mô hình đang khởi động',
        slow: 'Máy chủ mô hình đang khởi động',
        network: 'Không kết nối được máy chủ mô hình'
      }[engine?.reason] || 'Máy chủ mô hình không phản hồi';
      return this._unavailableResult(modelVersion, `${why} và dịch vụ Gemini cũng chưa phản hồi. Vui lòng thử lại sau ít phút.`, base);
    }

    // ---- Gemini báo ảnh không phù hợp ----
    if (G && G.verdict === 'not_lychee' && !(E && !E.uncertain && E.top !== 'Other')) {
      return this._unavailableResult(modelVersion,
        `Ảnh này có vẻ không phải lá vải${G.image_check?.subject ? ` (AI thấy: ${G.image_check.subject})` : ''}. Hãy chụp rõ một lá kép hoặc lá chét vải.`,
        { ...base, not_lychee: true, source: 'gemini', source_label: 'Gemini Vision' });
    }
    if (G && G.verdict === 'retake' && !(E && !E.uncertain)) {
      return this._unavailableResult(modelVersion,
        G.retake_advice || 'Ảnh chưa đủ rõ để chẩn đoán chắc chắn. Hãy chụp lại gần hơn, đủ sáng, lá chiếm phần lớn khung hình.',
        { ...base, retake: true, source: 'gemini', source_label: 'Gemini Vision', evidence: G.observed_symptoms || [] });
    }

    // ---- Trộn phân bố xác suất ----
    const dist = {};
    const add = (list, w) => (list || []).forEach((r) => { dist[r.class] = (dist[r.class] || 0) + w * Number(r.probability || 0); });
    let source;
    let agree = null;
    if (E && G) {
      add(E.results, 0.4);
      add(G.ranked, 0.6);
      agree = E.top === G.primary;
      source = 'model+gemini';
    } else if (E) {
      add(E.results, 1);
      source = 'model';
    } else {
      add(G.ranked, 1);
      source = 'gemini';
    }
    const ranked = Object.entries(dist).sort((a, b) => b[1] - a[1]);
    const [topCls, topP] = ranked[0];
    const secondP = ranked[1]?.[1] || 0;
    const healthy = this._isHealthy(topCls);
    const isOther = topCls === 'Other';
    const uncertain = (source === 'model' ? Boolean(E.uncertain) : topP < 55 || topP - secondP < 12) || agree === false;
    const severity = G && G.primary === topCls ? G.severity : null;

    const primary = healthy || isOther ? null : this._diseaseEntry(topCls, topP, severity);
    const secondary = ranked.slice(1)
      .filter(([c, p]) => p >= 20 && c !== 'Other' && !this._isHealthy(c) && this._lookup(c))
      .map(([c, p]) => this._diseaseEntry(c, p, null));

    // Khoanh vùng vết bệnh từ Gemini (box chuẩn hoá [ymin, xmin, ymax, xmax] 0..1)
    const detections = (G?.lesions || [])
      .filter((l) => !healthy && l.label !== 'Other' && this._lookup(l.label))
      .map((l) => {
        const d = this._lookup(l.label) || {};
        return { class: l.label, name_vi: d.name_vi || l.label, color: d.color || '#ea580c', box: l.box };
      });

    const SOURCE_LABEL = {
      model: `Mô hình LEAF_AI ${E?.model?.arch || ''}`.trim(),
      gemini: 'Gemini Vision (mô hình chưa sẵn sàng)',
      'model+gemini': agree ? 'Mô hình LEAF_AI + Gemini (đồng thuận)' : 'Mô hình LEAF_AI + Gemini (chưa thống nhất)'
    };

    const notes = [];
    if (source === 'gemini') {
      notes.push(engine?.reason === 'legacy_model' || engine?.reason === 'not_ready'
        ? 'Máy chủ chưa có mô hình lá vải mới nên kết quả do Gemini Vision phân tích.'
        : 'Máy chủ mô hình đang khởi động nên kết quả do Gemini Vision phân tích.');
    }
    if (agree === false) {
      const eName = this._lookup(E.top)?.name_vi || E.top;
      const gName = this._lookup(G.primary)?.name_vi || G.primary;
      notes.push(`Mô hình nghiêng về "${eName}", Gemini nghiêng về "${gName}". Hãy đối chiếu triệu chứng bên dưới, chụp thêm mặt dưới lá hoặc hỏi cán bộ BVTV.`);
    } else if (uncertain && !healthy) {
      notes.push('Độ chắc chắn chưa cao — nên chụp thêm 1–2 ảnh khác (gần hơn, cả mặt dưới lá) để xác nhận.');
    }
    if (isOther) {
      notes.push(G?.reasoning || 'Triệu chứng không khớp 5 bệnh hại trong danh mục (có thể do cháy nắng, thiếu dinh dưỡng, sâu ăn lá…).');
    }

    return {
      success: true,
      id: Date.now(),
      model_version: modelVersion,
      model_badge: SOURCE_LABEL[source],
      source,
      source_label: SOURCE_LABEL[source],
      agreement: agree,
      uncertain,
      other: isOther,
      healthy,
      is_coinfection: !healthy && !isOther && secondary.length > 0,
      warning_banner: secondary.length > 0 ? 'Nghi đồng nhiễm' : null,
      primary_disease: primary,
      secondary_diseases: secondary,
      heatmap_base64: E?.heatmap_base64
        ? (E.heatmap_base64.startsWith('data:') ? E.heatmap_base64 : `data:image/jpeg;base64,${E.heatmap_base64}`)
        : null,
      detections,
      lesion_count: detections.length,
      affected_area_percent: G?.affected_area_percent ?? null,
      evidence: G?.observed_symptoms || [],
      reasoning: G && !isOther ? G.reasoning : '',
      retake_advice: G?.retake_advice || '',
      model_confidence: E ? E.confidence : null,
      gemini_confidence: G ? G.confidence : null,
      note: notes.join(' '),
      ...base
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

  /**
   * Gửi câu hỏi tới chatbot. Thử lần lượt:
   *  - /api/chat   : Vercel Serverless Function (frontend/api/chat.js → Gemini)
   *  - /api/chat/  : FastAPI / Django backend (chạy local hoặc Render)
   * Không phụ thuộc /health/ vì bản deploy tĩnh không có route đó.
   * Lỗi mạng / 404 / 5xx → trả lời ngoại tuyến từ kho tri thức cục bộ.
   * @param {string} message
   * @param {{role:'user'|'model', text:string}[]} history
   * @param {{signal?: AbortSignal}} opts
   */
  async sendChatMessage(message, history = [], { signal } = {}) {
    const body = JSON.stringify({ message, history: Array.isArray(history) ? history.slice(-10) : [] });
    const paths = this.baseUrl ? ['/api/chat/', '/api/chat'] : ['/api/chat', '/api/chat/'];

    for (const path of paths) {
      try {
        const res = await this._fetch(path, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body,
          signal
        }, 45000);

        if (res.status === 429) {
          return { reply: 'Bà con gửi hơi nhanh. Đợi khoảng một phút rồi hỏi tiếp nhé.', rateLimited: true };
        }
        if (res.ok) {
          const json = await res.json().catch(() => null);
          if (json && (json.reply || json.reply_html)) return json;
        }
        // 404/405 (route không tồn tại), 503 (chưa có API key), 5xx → thử path kế tiếp
      } catch (err) {
        if (signal?.aborted) throw err; // người dùng chủ động huỷ
        console.warn(`[LEAF_AI] Chatbot ${path} lỗi:`, err?.name || err);
      }
    }

    return { reply_html: await this.offlineAnswer(message), offline: true };
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

  async googleLogin(email, fullName = '', avatarUrl = '') {
    if (!(await this.isOnline())) {
      throw new Error('Máy chủ đang ngoại tuyến. Vui lòng thử lại sau.');
    }
    const res = await this._fetch('/api/auth/google/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, full_name: fullName, avatar_url: avatarUrl })
    }, 10000);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || 'Đăng nhập Google không thành công.');
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
  async offlineAnswer(message) {
    await this._ensureLeafData();
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
    const d = hit && typeof LEAF_DATA !== 'undefined'
      ? Object.values(LEAF_DATA.diseases).find((x) => x.id === hit[0])
      : null;
    if (d) {
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
   * Phân tích quang học sắc tố mô lá phía client (diệp lục, đốm hoại tử, nhung đỏ)
   * Giúp nhận diện chính xác lá khỏe mạnh ngay cả khi chạy mô phỏng.
   */
  _analyzeImageOptically(imageSrc) {
    return new Promise((resolve) => {
      if (!imageSrc || typeof imageSrc !== 'string') {
        return resolve({ healthy: true, greenRatio: 0.95 });
      }
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        try {
          const canvas = document.createElement('canvas');
          const size = 120;
          canvas.width = size;
          canvas.height = size;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0, size, size);
          const data = ctx.getImageData(0, 0, size, size).data;

          let leafCount = 0;
          let greenCount = 0;
          let brownCount = 0;
          let redVelvetCount = 0;
          let darkCount = 0;
          let lesionX = [], lesionY = [];

          for (let i = 0; i < data.length; i += 4) {
            const r = data[i];
            const g = data[i + 1];
            const b = data[i + 2];

            // Loại bỏ nền quá sáng (trắng) hoặc quá tối (đen)
            if ((r > 225 && g > 225 && b > 225) || (r < 25 && g < 25 && b < 25)) continue;
            leafCount++;

            if (g > r * 1.05 && g > b * 1.05) {
              greenCount++;
            } else if (r > g * 1.1 && r > b * 1.1 && r > 75 && g < 145) {
              brownCount++;
              lesionX.push((i / 4) % size);
              lesionY.push(Math.floor((i / 4) / size));
            } else if (r > 115 && g < 85 && b < 80) {
              redVelvetCount++;
              lesionX.push((i / 4) % size);
              lesionY.push(Math.floor((i / 4) / size));
            } else if (r < 65 && g < 65 && b < 65) {
              darkCount++;
              lesionX.push((i / 4) % size);
              lesionY.push(Math.floor((i / 4) / size));
            }
          }

          const total = leafCount || 1;
          const greenRatio = greenCount / total;
          const brownRatio = brownCount / total;
          const erinoseRatio = redVelvetCount / total;
          const darkRatio = darkCount / total;

          // Lá vải xanh diệp lục tươi tốt, không có tổn thương mô hoại tử
          if (greenRatio >= 0.70 && brownRatio < 0.035 && erinoseRatio < 0.02 && darkRatio < 0.035) {
            return resolve({ healthy: true, greenRatio });
          }

          let diseaseCls = 'Anthracnose';
          let prob = 78;
          if (erinoseRatio > 0.04) {
            diseaseCls = 'Erinose';
            prob = Math.round(80 + erinoseRatio * 20);
          } else if (darkRatio > 0.07) {
            diseaseCls = 'Downy_blight';
            prob = Math.round(78 + darkRatio * 15);
          } else if (brownRatio > 0.04) {
            diseaseCls = 'Anthracnose';
            prob = Math.round(76 + brownRatio * 25);
          }

          let box = null;
          if (lesionX.length > 15) {
            const imgW = img.naturalWidth || 640;
            const imgH = img.naturalHeight || 640;
            const xmin = Math.min(...lesionX) / size;
            const xmax = Math.max(...lesionX) / size;
            const ymin = Math.min(...lesionY) / size;
            const ymax = Math.max(...lesionY) / size;
            box = [
              Math.round(xmin * imgW),
              Math.round(ymin * imgH),
              Math.max(30, Math.round((xmax - xmin) * imgW)),
              Math.max(30, Math.round((ymax - ymin) * imgH))
            ];
          }

          resolve({
            healthy: false,
            diseaseClass: diseaseCls,
            confidence: Math.min(95, Math.max(68, prob)),
            box
          });
        } catch {
          resolve({ healthy: true, greenRatio: 0.9 });
        }
      };
      img.onerror = () => resolve({ healthy: true, greenRatio: 0.9 });
      img.src = imageSrc;
    });
  }

  /**
   * Kết quả mô phỏng cho ảnh mẫu minh họa hoặc ảnh tải lên khi máy chủ ngoại tuyến.
   */
  async simulateDetection(modelVersion, image) {
    const src = typeof image === 'string' ? image : '';
    const sampleKey = (src.match(/sample_([a-z_]+)\.jpg/) || [])[1] || 'upload';

    const PROFILES = {
      anthracnose: { main: ['Anthracnose', 91], second: ['Leaf_blight', 6], boxes: [[337, 214, 84, 84], [459, 369, 84, 84], [461, 12, 106, 106], [337, 491, 101, 101]] },
      downy_blight: { main: ['Downy_blight', 88], second: ['Anthracnose', 9], boxes: [[311, 193, 105, 105], [458, 86, 115, 115]] },
      leaf_blight: { main: ['Leaf_blight', 62], second: ['Anthracnose', 31], boxes: [[180, 304, 67, 84], [482, 352, 112, 82]] },
      algal_spot: { main: ['Algal_spot', 94], second: null, boxes: [[273, 483, 91, 80], [317, 200, 77, 93], [471, 117, 80, 97]] },
      erinose: { main: ['Erinose', 90], second: null, boxes: [[177, 349, 92, 92], [302, 215, 106, 106], [456, 356, 92, 92]] },
      healthy: null
    };

    const base = { success: true, simulated: true, sample: sampleKey !== 'upload', id: Date.now(), model_version: modelVersion };

    // Xử lý ảnh tải lên từ máy của người dùng
    if (sampleKey === 'upload') {
      const optical = await this._analyzeImageOptically(src);
      if (optical.healthy) {
        return {
          ...base,
          healthy: true,
          primary_disease: null,
          secondary_diseases: [],
          detections: [],
          lesion_count: 0,
          is_coinfection: false,
          note: 'Lá vải thiều phát triển xanh tốt, bề mặt nhẵn mịn, không phát hiện dấu hiệu của 5 bệnh hại nguy hiểm.'
        };
      }

      const d = this._lookup(optical.diseaseClass) || {};
      const sev = (p) => (p >= 60 ? 'Nghiêm trọng' : p >= 35 ? 'Trung bình' : 'Nhẹ');
      const primary = {
        class: optical.diseaseClass,
        id: d.id,
        name_en: d.name_en || optical.diseaseClass,
        name_vi: d.name_vi || optical.diseaseClass,
        probability: optical.confidence,
        severity: sev(optical.confidence),
        color: d.color || '#ea580c',
        treatment: d.treatment || {}
      };

      const detections = optical.box ? [{
        class: primary.class,
        name_vi: primary.name_vi,
        confidence: primary.probability / 100,
        probability_percent: primary.probability,
        color: primary.color,
        bbox: optical.box
      }] : [];

      return {
        ...base,
        healthy: false,
        primary_disease: primary,
        secondary_diseases: [],
        detections,
        lesion_count: detections.length,
        is_coinfection: false,
        heatmap_url: null,
        note: 'Kết quả phân tích trắc quang mô lá cho thấy dấu hiệu bệnh hại.'
      };
    }

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

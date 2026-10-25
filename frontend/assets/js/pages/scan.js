/**
 * LEAF_AI — Trang quét lá (scan.html), giao diện v3 tinh gọn:
 *   Ảnh lá  →  Kết quả (tên bệnh, độ tin cậy, việc cần làm)  →  Hỏi kỹ sư AI ngay bên dưới (đã biết bệnh vừa quét).
 * Toàn bộ bất đồng bộ (Promise / AbortController), không chặn giao diện.
 */
(function () {
  'use strict';
  const { diseases, escapeHtml, toast, history, makeThumb, mdToHtml } = window.Leaf;

  const $ = (id) => document.getElementById(id);
  const api = new LeafApiService();
  const renderer = new LeafCanvasRenderer($('scanCanvas'));

  const STAGE_TEXT = {
    prepare: 'Đang kiểm tra ảnh…',
    model: 'AI đang phân tích lá…',
    second_opinion: 'Ca khó — đang kiểm tra chéo thêm…',
    done: 'Đang tổng hợp kết quả…'
  };
  const SEV_COLOR = { 'Nghiêm trọng': '#d4452a', 'Trung bình': '#c98a12', 'Nhẹ': '#1e7a4c' };
  const SAMPLE_SRC = 'assets/samples/sample_anthracnose.jpg';

  const state = { model: 'v4', src: null, runId: 0, busy: false, surface: '', result: null };

  // ------------------------------------------------------------------
  // Tiện ích giao diện
  // ------------------------------------------------------------------
  const loadImage = (src) => new Promise((resolve) => renderer.setImage(src, resolve));
  const playScan = (ms) => new Promise((resolve) => renderer.startScanning(ms, resolve));
  const shortName = (name) => String(name || '').split(' (')[0];

  function setStatus(kind, text) {
    const el = $('resultStatus');
    el.classList.toggle('is-busy', kind === 'busy');
    el.classList.toggle('is-done', kind === 'done');
    el.classList.toggle('is-warn', kind === 'warn');
    $('resultStatusText').textContent = text;
  }

  function setBusy(busy) {
    state.busy = busy;
    ['btnOpenCamera', 'btnPickFile'].forEach((id) => ($(id).disabled = busy));
    $('dropZone').setAttribute('aria-busy', String(busy));
  }

  function setViewMode(mode) {
    const heat = mode === 'heatmap';
    renderer.toggleHeatmap(heat);
    $('btnModeBox').setAttribute('aria-pressed', String(!heat));
    $('btnModeHeatmap').setAttribute('aria-pressed', String(heat));
  }

  // ------------------------------------------------------------------
  // Chẩn đoán
  // ------------------------------------------------------------------
  async function runDiagnosis(src, { save = true } = {}) {
    if (!src) return;
    const runId = ++state.runId; // bỏ qua kết quả cũ nếu người dùng đổi ảnh giữa chừng
    state.src = src;
    setBusy(true);

    $('resultIntro').hidden = true;
    $('resultCard').hidden = false;
    $('resultBody').innerHTML = '<div class="scan3-skeleton" aria-hidden="true"><i></i><i></i><i></i></div>';
    setStatus('busy', STAGE_TEXT.prepare);
    ask.hide();

    try {
      await loadImage(src);
      $('dropZone').classList.add('has-image');
      $('viewToggle').hidden = true;
      if (window.matchMedia('(max-width: 979px)').matches) {
        $('resultCard').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }

      const [result] = await Promise.all([
        api.diagnose(src, state.model, {
          surface: state.surface,
          onStage: (st) => { if (runId === state.runId && STAGE_TEXT[st]) setStatus('busy', STAGE_TEXT[st]); }
        }),
        playScan(1600)
      ]);
      if (runId !== state.runId) return;
      state.result = result;

      // Ảnh: khung vết bệnh + bản đồ nhiệt (nếu có); lá khỏe không vẽ khung
      const heatmap = result.heatmap_base64 || result.heatmap_url || null;
      renderer.setDetections(result.healthy ? [] : (result.detections || []));
      renderer.setHeatmap(heatmap);
      $('viewToggle').hidden = !heatmap;
      setViewMode(heatmap && !result.healthy && !(result.detections || []).length ? 'heatmap' : 'box');

      renderResult(result);
      ask.start(result);
      if (save && !result.simulated) await saveRecord(result, src);
    } catch (err) {
      if (runId !== state.runId) return;
      renderer.stopScanning();
      setStatus('warn', 'Không phân tích được ảnh');
      $('resultBody').innerHTML = `<div class="scan3-state">
          <i class="bi bi-exclamation-circle"></i>
          <h3>Chưa phân tích được</h3>
          <p>${escapeHtml(err.message || 'Hãy thử lại sau ít phút.')}</p>
        </div>`;
      toast(err.message || 'Không phân tích được ảnh, hãy thử lại.');
    } finally {
      if (runId === state.runId) setBusy(false);
    }
  }

  // ------------------------------------------------------------------
  // Hiển thị kết quả (gọn: 1 kết luận + việc cần làm + hành động)
  // ------------------------------------------------------------------
  function renderResult(r) {
    const tips = [...new Set([...(r.quality_tips || []), ...(r.retake && r.retake_advice ? [r.retake_advice] : [])])];
    const tipsHtml = tips.length && !r.simulated
      ? `<div class="scan3-tip"><i class="bi bi-camera"></i><div>${tips.map((t) => escapeHtml(t)).join('<br>')}</div></div>`
      : '';
    const sourceHtml = r.simulated
      ? '<span class="scan3-source"><i class="bi bi-info-circle"></i>Ảnh minh họa — kết quả mô phỏng</span>'
      : `<span class="scan3-source"><i class="bi bi-cpu"></i>${escapeHtml(r.source_label || 'LEAF_AI')}</span>`;
    const why = r.reasoning
      ? `<details class="scan3-why"><summary>Vì sao AI kết luận vậy?</summary><p>${escapeHtml(r.reasoning)}</p></details>`
      : '';

    // ---- Không phân tích được / không phải lá vải / cần chụp lại ----
    if (r.analysis_unavailable) {
      const title = r.not_lychee ? 'Không nhận ra lá vải' : r.retake ? 'Cần chụp lại ảnh' : 'Chưa phân tích được';
      setStatus('warn', title);
      $('resultBody').innerHTML = `${tipsHtml}
        <div class="scan3-state">
          <i class="bi ${r.not_lychee ? 'bi-question-circle' : r.retake ? 'bi-camera' : 'bi-cloud-slash'}"></i>
          <h3>${title}</h3>
          <p>${escapeHtml(r.note || 'Vui lòng thử lại sau ít phút.')}</p>
          <button class="btn btn-primary" type="button" data-action="retake"><i class="bi bi-camera"></i>Chụp lại</button>
        </div>
        <div class="scan3-foot">${sourceHtml}</div>`;
      return;
    }

    const evidence = (r.evidence || []).slice(0, 3);
    const evidenceHtml = evidence.length
      ? `<ul class="scan3-evidence">${evidence.map((e) => `<li><i class="bi bi-check2"></i>${escapeHtml(e)}</li>`).join('')}</ul>`
      : '';
    const warn = r.agreement === false || r.uncertain;
    const noteHtml = r.note
      ? `<p class="scan3-note${warn ? ' is-warn' : ''}"><i class="bi ${warn ? 'bi-exclamation-triangle' : 'bi-info-circle'}"></i>${escapeHtml(r.note)}</p>`
      : '';

    // ---- Vấn đề khác (không thuộc 5 bệnh) ----
    if (r.other) {
      setStatus('warn', 'Không khớp 5 bệnh thường gặp');
      $('resultBody').innerHTML = `${tipsHtml}
        <div class="scan3-verdict">
          <div class="scan3-verdict-main">
            <span class="scan3-badge is-mid">Cần kiểm tra thêm</span>
            <h3 class="scan3-name">Không thuộc 5 bệnh thường gặp</h3>
            <p class="scan3-latin">Có thể do cháy nắng, thiếu dinh dưỡng, sâu ăn lá, rệp/muội đen…</p>
          </div>
        </div>
        ${evidenceHtml}
        <div class="scan3-cta"><a class="btn btn-block" href="library.html"><i class="bi bi-journal-text"></i>Xem thư viện bệnh</a></div>
        <div class="scan3-foot">${sourceHtml}</div>`;
      return;
    }

    // ---- Lá khỏe ----
    if (r.healthy || !r.primary_disease) {
      setStatus('done', 'Không phát hiện bệnh');
      $('resultBody').innerHTML = `${tipsHtml}
        <div class="scan3-verdict is-healthy">
          <span class="scan3-healthy-icon"><i class="bi bi-check-lg"></i></span>
          <div class="scan3-verdict-main">
            <h3 class="scan3-name">Lá vải khỏe mạnh</h3>
            <p class="scan3-latin">Chưa thấy dấu hiệu của 5 bệnh hại thường gặp</p>
          </div>
        </div>
        <p class="scan3-todo"><strong>Nên làm:</strong> thăm vườn 1–2 lần/tuần, để ý lộc non và mặt dưới lá sau mưa phùn, nồm ẩm.</p>
        ${noteHtml}
        <div class="scan3-foot">${sourceHtml}</div>`;
      return;
    }

    // ---- Có bệnh ----
    const p = r.primary_disease;
    const info = diseases.find(p.class) || {};
    const pct = Math.round(p.probability);
    const color = SEV_COLOR[p.severity] || 'var(--crimson)';
    const sev = p.severity
      ? `<span class="scan3-badge ${p.severity === 'Nghiêm trọng' ? 'is-high' : p.severity === 'Trung bình' ? 'is-mid' : 'is-low'}">${escapeHtml(p.severity)}</span>`
      : '';
    const area = Number.isFinite(r.affected_area_percent) ? `<span class="scan3-chip">~${Math.round(r.affected_area_percent)}% diện tích lá</span>` : '';
    const secondary = (r.secondary_diseases || []).map((s) => `${escapeHtml(shortName(s.name_vi))} ${Math.round(s.probability)}%`).join(', ');
    const todo = info.treatment?.cultural || '';

    setStatus('done', r.uncertain ? 'Đã phân tích — nên chụp thêm để chắc chắn' : 'Đã nhận diện bệnh');
    $('resultBody').innerHTML = `${tipsHtml}
      <div class="scan3-verdict">
        <div class="scan3-verdict-main">
          <h3 class="scan3-name">${escapeHtml(shortName(p.name_vi || info.name_vi || p.class))}</h3>
          <p class="scan3-latin">${escapeHtml(info.pathogen || p.name_en || '')}</p>
          <div class="scan3-badges">${sev}${area}</div>
        </div>
        <div class="scan3-score" style="--score:${color}"><b>${pct}%</b><span>độ tin cậy</span></div>
      </div>
      <div class="meter" aria-hidden="true"><i id="primaryMeter" style="--bar:${color}"></i></div>
      ${noteHtml}
      ${evidenceHtml}
      ${todo ? `<p class="scan3-todo"><strong>Việc nên làm ngay:</strong> ${escapeHtml(todo)}</p>` : ''}
      ${secondary ? `<p class="scan3-also">Có thể kèm: ${secondary}</p>` : ''}
      <div class="scan3-cta">
        <a class="btn btn-primary btn-block" href="treatment.html?id=${encodeURIComponent(p.class)}&p=${pct}"><i class="bi bi-clipboard2-pulse"></i>Lập phác đồ điều trị</a>
        <a class="btn btn-block" href="${diseases.url(p.class)}"><i class="bi bi-journal-medical"></i>Chi tiết bệnh</a>
      </div>
      <div class="scan3-foot">${sourceHtml}${why}</div>`;
    requestAnimationFrame(() => { const m = $('primaryMeter'); if (m) m.style.width = `${pct}%`; });
  }

  async function saveRecord(result, src) {
    const p = result.primary_disease;
    const failed = Boolean(result.analysis_unavailable);
    const thumb = await makeThumb(src);
    history.add({
      id: result.id || Date.now(),
      timestamp: new Date().toISOString(),
      model: result.source_label || 'LEAF_AI',
      class: failed ? 'Unavailable' : result.other ? 'Other' : (p ? p.class : 'Healthy'),
      primary_disease: failed ? 'Chưa phân tích được' : result.other ? 'Vấn đề khác' : (p ? (p.name_vi || p.class) : 'Lá vải khỏe mạnh'),
      probability: p ? Math.round(p.probability) : 0,
      severity: failed || result.other ? '' : (p ? (p.severity || '') : 'Khỏe'),
      is_coinfection: Boolean(result.is_coinfection),
      secondary: (result.secondary_diseases || []).map((s) => s.name_vi || s.class),
      lesions: (result.detections || []).length,
      simulated: Boolean(result.simulated),
      synced_to_firebase: false,
      thumb
    });
  }

  // ------------------------------------------------------------------
  // Hỏi kỹ sư AI ngay dưới kết quả (biết sẵn bệnh vừa quét)
  // ------------------------------------------------------------------
  const ask = (() => {
    const card = $('askCard');
    const thread = $('askThread');
    const chips = $('askChips');
    const form = $('askForm');
    const input = $('askInput');
    const send = $('askSend');
    let messages = [];   // {who:'me'|'bot', html, text}
    let context = '';
    let sending = false;
    let ctrl = null;

    const scrollDown = () => requestAnimationFrame(() => { thread.scrollTop = thread.scrollHeight; });
    const syncSend = () => { send.disabled = sending || !input.value.trim(); };
    const plain = (html) => String(html || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();

    function add(who, html, text) {
      messages.push({ who, html, text });
      const el = document.createElement('div');
      el.className = `chat-msg ${who}`;
      el.innerHTML = `<div class="chat-bubble">${html}</div>`;
      thread.appendChild(el);
      scrollDown();
      return el;
    }

    function buildContext(r) {
      if (r.analysis_unavailable) return `Ảnh vừa quét chưa phân tích được (${r.not_lychee ? 'có thể không phải lá vải' : r.retake ? 'ảnh chưa rõ' : 'dịch vụ AI chưa phản hồi'}).`;
      const parts = [];
      if (r.other) parts.push('Kết quả: triệu chứng không khớp 5 bệnh thường gặp (vấn đề khác).');
      else if (r.healthy || !r.primary_disease) parts.push('Kết quả: lá vải khỏe, không thấy dấu hiệu bệnh.');
      else {
        const p = r.primary_disease;
        parts.push(`Kết quả: ${shortName(p.name_vi)} (${p.class}), độ tin cậy ${Math.round(p.probability)}%${p.severity ? `, mức ${p.severity}` : ''}${Number.isFinite(r.affected_area_percent) ? `, khoảng ${Math.round(r.affected_area_percent)}% diện tích lá tổn thương` : ''}.`);
        if ((r.secondary_diseases || []).length) parts.push(`Có thể kèm: ${r.secondary_diseases.map((s) => `${shortName(s.name_vi)} ${Math.round(s.probability)}%`).join(', ')}.`);
      }
      if ((r.evidence || []).length) parts.push(`Triệu chứng AI quan sát: ${r.evidence.slice(0, 4).join('; ')}.`);
      if (r.uncertain) parts.push('Kết quả chưa thật chắc chắn.');
      if (r.agreement === false) parts.push('Mô hình và Gemini chưa thống nhất.');
      if (state.surface) parts.push(`Ảnh chụp ${state.surface === 'bottom' ? 'mặt dưới' : 'mặt trên'} lá.`);
      if (r.simulated) parts.push('Đây là ảnh minh họa, kết quả mô phỏng.');
      return parts.join(' ');
    }

    function intro(r) {
      if (r.analysis_unavailable) {
        return { html: '<p>Em chưa đọc được ảnh này. Bà con có thể <strong>mô tả triệu chứng bằng lời</strong> (màu vết bệnh, vị trí trên lá, thời tiết gần đây), em vẫn tư vấn được.</p>',
          chips: ['Cách chụp lá vải cho AI nhận đúng?', 'Lá có đốm nâu, viền vàng là bệnh gì?', 'Mặt dưới lá có lớp nhung đỏ là gì?'] };
      }
      if (r.other) {
        return { html: '<p>Triệu chứng không khớp 5 bệnh thường gặp. Bà con mô tả thêm (màu vết, vị trí, thời tiết, đã bón phân/phun thuốc gì) để em đoán nguyên nhân nhé.</p>',
          chips: ['Lá như vậy có thể do đâu?', 'Có phải do thiếu dinh dưỡng không?', 'Có cần mời cán bộ BVTV không?'] };
      }
      if (r.healthy || !r.primary_disease) {
        return { html: '<p>Lá trong ảnh trông <strong>khỏe</strong>, chưa thấy dấu hiệu bệnh. Bà con cần tư vấn chăm sóc giai đoạn này không?</p>',
          chips: ['Giai đoạn này cần chăm sóc gì?', 'Khi nào nên phun phòng bệnh?', 'Dấu hiệu bệnh sớm cần để ý?'] };
      }
      const p = r.primary_disease;
      const name = shortName(p.name_vi);
      const unsure = r.uncertain ? ' Kết quả chưa thật chắc chắn, bà con mô tả thêm triệu chứng để em tư vấn kỹ hơn.' : '';
      return {
        html: `<p>Em đã xem ảnh: khả năng cao lá bị <strong>${escapeHtml(name)}</strong> (${Math.round(p.probability)}%).${unsure} Bà con muốn hỏi gì thêm?</p>`,
        chips: [`Xử lý ${name.toLowerCase()} thế nào cho đúng?`, 'Dùng thuốc gì, khi nào phun?', 'Làm sao để không lây sang cây khác?', 'Bao lâu thì kiểm tra lại?']
      };
    }

    function renderChips(list) {
      chips.innerHTML = list.map((q) => `<button type="button" class="chat-chip" data-q="${escapeHtml(q)}">${escapeHtml(q)}</button>`).join('');
      chips.hidden = list.length === 0;
    }

    function start(r) {
      if (ctrl) ctrl.abort();
      ctrl = null;
      sending = false;
      messages = [];
      thread.replaceChildren();
      context = buildContext(r);
      const { html, chips: list } = intro(r);
      $('askSub').textContent = r.analysis_unavailable
        ? 'Mô tả triệu chứng, em tư vấn ngay'
        : r.simulated ? 'Đang dùng kết quả ảnh minh họa' : 'Đã nắm kết quả quét của bạn';
      add('bot', html, plain(html));
      renderChips(list);
      input.value = '';
      autoGrow();
      syncSend();
      card.hidden = false;
      document.body.classList.add('has-inline-chat');
    }

    function hide() {
      if (ctrl) ctrl.abort();
      ctrl = null;
      sending = false;
      card.hidden = true;
      document.body.classList.remove('has-inline-chat');
    }

    async function submit(text) {
      const msg = String(text ?? input.value).trim();
      if (!msg || sending) return;
      sending = true;
      if (text === undefined) { input.value = ''; autoGrow(); }
      syncSend();
      chips.hidden = true;
      const turns = messages.filter((m) => m.text).slice(-10).map((m) => ({ role: m.who === 'me' ? 'user' : 'model', text: m.text }));
      add('me', `<p>${escapeHtml(msg)}</p>`, msg);
      const typing = add('bot', '<span class="typing-dots" aria-label="Đang trả lời"><i></i><i></i><i></i></span>', '');
      messages.pop(); // bong bóng "đang gõ" không vào lịch sử
      const local = new AbortController();
      ctrl = local;
      try {
        const res = await api.sendChatMessage(msg, turns, { signal: local.signal, context });
        if (local.signal.aborted) return;
        typing.remove();
        if (res.offline) {
          add('bot', `${res.reply_html}<p class="chat-offline"><i class="bi bi-journal-bookmark"></i>Trả lời từ kho kiến thức ngoại tuyến</p>`, plain(res.reply_html));
        } else {
          add('bot', mdToHtml(res.reply || '') || '<p>Em chưa có dữ liệu cho câu hỏi này.</p>', res.reply || '');
        }
      } catch (err) {
        typing.remove();
        if (!local.signal.aborted) add('bot', '<p>Em chưa gửi được câu hỏi. Bà con kiểm tra mạng rồi thử lại nhé.</p>', '');
      } finally {
        if (ctrl === local) {
          ctrl = null;
          sending = false;
          syncSend();
        }
      }
    }

    function autoGrow() {
      input.style.height = 'auto';
      input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
    }

    form.addEventListener('submit', (e) => { e.preventDefault(); submit(); });
    input.addEventListener('input', () => { autoGrow(); syncSend(); });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); submit(); }
    });
    chips.addEventListener('click', (e) => {
      const b = e.target.closest('[data-q]');
      if (b) submit(b.dataset.q);
    });

    // Nút "Kỹ sư AI" (bottom nav / bong bóng) trên trang này: cuộn tới khung chat của kết quả
    window.Leaf.onChatButton = () => {
      if (card.hidden) return false;
      card.scrollIntoView({ behavior: 'smooth', block: 'start' });
      setTimeout(() => input.focus({ preventScroll: true }), 450);
      return true;
    };

    return { start, hide };
  })();

  // ------------------------------------------------------------------
  // Nguồn ảnh: camera, file, ảnh minh họa
  // ------------------------------------------------------------------
  const cameraDialog = $('cameraDialog');
  const camera = new LeafCameraManager({
    videoElement: $('cameraVideo'),
    onImageCaptured: (base64) => runDiagnosis(base64)
  });
  camera.initDropZone($('dropZone'), $('fileInput'));

  // Đã có ảnh: chạm vào ảnh không mở hộp chọn file (tránh bấm nhầm khi đang xem kết quả)
  document.querySelector('.scan3-capture').addEventListener('click', (e) => {
    const stage = $('dropZone');
    if (stage.classList.contains('has-image') && stage.contains(e.target) && !e.target.closest('button')) e.stopPropagation();
  }, true);

  $('btnPickFile').addEventListener('click', () => $('fileInput').click());
  $('btnTrySample').addEventListener('click', () => runDiagnosis(SAMPLE_SRC, { save: false }));

  async function openCamera() {
    cameraDialog.showModal();
    try {
      await camera.startCamera();
    } catch (err) {
      cameraDialog.close();
      toast(err.name === 'NotAllowedError'
        ? 'Bạn chưa cho phép dùng camera. Hãy bật quyền camera hoặc chọn ảnh từ máy.'
        : 'Không mở được camera. Hãy chọn ảnh từ máy thay thế.');
    }
  }
  $('btnOpenCamera').addEventListener('click', openCamera);
  $('resultBody').addEventListener('click', (e) => {
    if (e.target.closest('[data-action="retake"]')) openCamera();
  });
  $('btnFlipCamera').addEventListener('click', () => camera.toggleFacingMode().catch(() => toast('Thiết bị chỉ có một camera.')));
  $('btnSnapPhoto').addEventListener('click', () => {
    camera.captureSnapshot();
    cameraDialog.close();
  });
  cameraDialog.querySelectorAll('[data-close]').forEach((b) => b.addEventListener('click', () => cameraDialog.close()));
  cameraDialog.addEventListener('close', () => camera.stopCamera());

  $('btnModeBox').addEventListener('click', () => setViewMode('box'));
  $('btnModeHeatmap').addEventListener('click', () => setViewMode('heatmap'));

  // Mặt lá trong ảnh: giúp phân biệt nhện lông nhung (mặt dưới) với đốm rong (mặt trên)
  const surfaceButtons = [...document.querySelectorAll('#surfaceGroup [data-surface]')];
  surfaceButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      state.surface = btn.dataset.surface;
      surfaceButtons.forEach((b) => b.setAttribute('aria-pressed', String(b === btn)));
    });
  });

  // Vẽ lại canvas khi đổi kích thước (gom bằng requestAnimationFrame)
  let raf = 0;
  window.addEventListener('resize', () => {
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => { renderer.resizeCanvas(); renderer.render(); });
  });

  api.warmUpEngine(); // đánh thức máy chủ mô hình trên Render ngay khi mở trang
})();

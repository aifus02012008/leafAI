/**
 * LEAF_AI — Trang chẩn đoán (scan.html)
 * Luồng: chọn ảnh → quét (animation chạy song song với gọi API) → khoanh vùng → kết quả → phác đồ.
 * Toàn bộ bất đồng bộ bằng Promise, không chặn luồng giao diện.
 */
(function () {
  'use strict';
  const { diseases, sevBadge, escapeHtml, toast, history, makeThumb } = window.Leaf;

  const $ = (id) => document.getElementById(id);
  const api = new LeafApiService();
  const renderer = new LeafCanvasRenderer($('scanCanvas'));

  const MODELS = {
    v3: { label: 'V3', classes: '3', map: '0.768', recall: '80.8%' },
    v4: { label: 'V4', classes: '6', map: '0.742', recall: '79.1%' }
  };
  const SEV_COLOR = { 'Nghiêm trọng': '#d4452a', 'Trung bình': '#e8b33c', 'Nhẹ': '#1e7a4c' };

  const state = { model: 'v3', src: null, runId: 0, busy: false };

  // ------------------------------------------------------------------
  // Helpers
  // ------------------------------------------------------------------
  const loadImage = (src) => new Promise((resolve) => renderer.setImage(src, resolve));
  const playScan = (ms) => new Promise((resolve) => renderer.startScanning(ms, resolve));

  function setStep(n) {
    [...$('stepper').children].forEach((li, i) => {
      li.classList.toggle('is-done', i + 1 < n);
      li.classList.toggle('is-active', i + 1 === n);
    });
  }

  function setStatus(kind, text) {
    const el = $('resultStatus');
    el.classList.toggle('is-busy', kind === 'busy');
    el.classList.toggle('is-done', kind === 'done');
    $('resultStatusText').textContent = text;
  }

  function setBusy(busy) {
    state.busy = busy;
    ['btnRescan', 'btnOpenCamera', 'btnPickFile'].forEach((id) => ($(id).disabled = busy));
  }

  function setViewMode(mode) {
    state.viewMode = mode;
    const isHeatmap = mode === 'heatmap';
    renderer.toggleHeatmap(isHeatmap);
    const btnBox = $('btnModeBox');
    const btnHeatmap = $('btnModeHeatmap');
    if (btnBox && btnHeatmap) {
      btnBox.setAttribute('aria-pressed', String(!isHeatmap));
      btnHeatmap.setAttribute('aria-pressed', String(isHeatmap));
    }
  }

  // ------------------------------------------------------------------
  // Chẩn đoán
  // ------------------------------------------------------------------
  async function runDiagnosis(src, { save = true } = {}) {
    if (!src) return;
    const runId = ++state.runId; // bỏ qua kết quả cũ nếu người dùng đổi ảnh giữa chừng
    state.src = src;
    setBusy(true);
    setStep(2);
    setStatus('busy', `AI đang phân tích bằng mô hình ${MODELS[state.model].label}…`);

    try {
      await loadImage(src);
      $('dropZone').classList.add('has-image');
      const [result] = await Promise.all([api.diagnose(src, state.model), playScan(1700)]);
      if (runId !== state.runId) return;

      setStep(3);
      renderer.setDetections(result.detections || []);

      const heatmapSrc = result.heatmap_base64 || result.heatmap_url || null;
      if (heatmapSrc) {
        renderer.setHeatmap(heatmapSrc);
        if ($('viewModeBar')) $('viewModeBar').hidden = false;
        setViewMode('box');
      } else {
        renderer.setHeatmap(null);
        if ($('viewModeBar')) $('viewModeBar').hidden = true;
      }

      renderResult(result);
      setStep(4);
      setStatus('done', result.analysis_unavailable
        ? 'Chưa phân tích được — hãy thử lại sau'
        : result.healthy
          ? 'Không phát hiện vết bệnh'
          : `Đã khoanh vùng ${result.lesion_count ?? (result.detections || []).length} vết bệnh`);

      if (save) await saveRecord(result, src);
    } catch (err) {
      if (runId !== state.runId) return;
      renderer.stopScanning();
      setStep(1);
      setStatus('', err.message || 'Không phân tích được ảnh, hãy thử lại.');
      toast(err.message || 'Không phân tích được ảnh, hãy thử lại.');
    } finally {
      if (runId === state.runId) setBusy(false);
    }
  }

  function renderResult(result) {
    $('resultEmpty').hidden = true;
    $('resultBody').hidden = false;

    const primary = result.primary_disease;
    const secondary = result.secondary_diseases || [];
    const healthy = result.healthy || !primary;

    $('coinfectionAlert').hidden = !result.is_coinfection;

    const notes = [];
    if (result.simulated) notes.push('Chưa kết nối máy chủ AI nên đang chạy chế độ mô phỏng. Kết quả chỉ để minh họa.');
    if (result.note) notes.push(result.note);
    $('noteAlert').hidden = notes.length === 0;
    $('noteText').textContent = notes.join(' ');

    // Báo cáo HTML chi tiết từ AI (backend đã sanitize) — hiển thị nguyên khối
    const reportSection = $('aiReportSection');
    const reportBox = $('aiReport');
    if (result.report_html) {
      reportBox.innerHTML = result.report_html;
      reportSection.hidden = false;
    } else {
      reportBox.innerHTML = '';
      reportSection.hidden = true;
    }

    if (result.analysis_unavailable) {
      // AI không phân tích được — không được láo "Lá khỏe mạnh"
      $('primaryName').textContent = 'Chưa phân tích được ảnh';
      $('primaryLatin').textContent = 'Dịch vụ AI đang gián đoạn hoặc chưa được cấu hình.';
      $('primarySeverity').innerHTML = '';
      $('primaryScore').textContent = '—';
      $('primaryScore').style.color = 'var(--ink-3)';
      $('primaryMeter').style.width = '0%';
      $('primaryNote').textContent = result.note || 'Vui lòng thử lại sau ít phút.';
      $('secondaryWrap').hidden = true;
      $('btnProtocol').href = 'library.html';
      $('btnProtocol').innerHTML = '<i class="bi bi-journal-medical"></i>Xem thư viện bệnh';
      $('btnAsk').href = 'assistant.html';
      return;
    }

    if (healthy) {
      $('primaryName').textContent = 'Lá khỏe mạnh';
      $('primaryLatin').textContent = 'Không thấy vết bệnh mô hình nhận diện được';
      $('primarySeverity').innerHTML = '<span class="sev sev-low">Khỏe</span>';
      $('primaryScore').textContent = '—';
      $('primaryScore').style.color = 'var(--leaf)';
      $('primaryMeter').style.width = '0%';
      $('primaryNote').textContent = 'Tiếp tục thăm vườn 2 lần mỗi tuần, chú ý mặt dưới lá già sau những ngày mưa ẩm.';
      $('secondaryWrap').hidden = true;
      $('btnProtocol').href = 'handbook.html#kiem-tra';
      $('btnProtocol').innerHTML = '<i class="bi bi-shield-check"></i>Xem quy trình kiểm tra vườn';
      $('btnAsk').href = 'assistant.html';
      return;
    }

    const info = diseases.find(primary.class) || {};
    const pct = Math.round(primary.probability);
    const color = SEV_COLOR[primary.severity] || '#d4452a';

    $('primaryName').textContent = primary.name_vi || info.name_vi || primary.class;
    $('primaryLatin').textContent = [primary.name_en || info.name_en, info.pathogen].filter(Boolean).join(', ');
    $('primarySeverity').innerHTML = sevBadge(primary.severity);
    $('primaryScore').textContent = `${pct}%`;
    $('primaryScore').style.color = color;
    $('primaryMeter').style.setProperty('--bar', color);
    requestAnimationFrame(() => ($('primaryMeter').style.width = `${pct}%`));
    $('primaryNote').innerHTML = info.treatment
      ? `<strong>Việc nên làm ngay:</strong> ${escapeHtml(info.treatment.cultural)}`
      : '';

    $('secondaryWrap').hidden = secondary.length === 0;
    $('secondaryList').innerHTML = secondary.map((s) => {
      const d = diseases.find(s.class) || {};
      return `<li>
        <span class="dot" style="--dot:${escapeHtml(s.color || d.color || '#999')}"></span>
        <a href="${diseases.url(s.class)}">${escapeHtml(s.name_vi || d.name_vi || s.class)}</a>
        <span class="pct">${Math.round(s.probability)}%</span>
        ${sevBadge(s.severity)}
      </li>`;
    }).join('');

    $('btnProtocol').href = diseases.url(primary.class);
    $('btnProtocol').innerHTML = `<i class="bi bi-journal-medical"></i>Xem phác đồ ${escapeHtml(info.name_vi ? info.name_vi.split(' (')[0].toLowerCase() : 'xử lý')}`;
    const q = `Lá cà chua của tôi được chẩn đoán ${primary.name_vi || primary.class} (${pct}%)${secondary.length ? ', kèm ' + secondary.map((s) => s.name_vi).join(', ') : ''}. Tôi nên xử lý thế nào?`;
    $('btnAsk').href = `assistant.html?q=${encodeURIComponent(q)}`;
  }

  async function saveRecord(result, src) {
    const p = result.primary_disease;
    const failed = Boolean(result.analysis_unavailable);
    const thumb = await makeThumb(src);
    history.add({
      id: result.id || Date.now(),
      timestamp: new Date().toISOString(),
      model: result.model_version || state.model,
      class: failed ? 'Unavailable' : (p ? p.class : 'Healthy'),
      primary_disease: failed ? 'Chưa phân tích được' : (p ? (p.name_vi || p.class) : 'Lá khỏe mạnh'),
      probability: p ? Math.round(p.probability) : 0,
      severity: failed ? '' : (p ? p.severity : 'Khỏe'),
      is_coinfection: Boolean(result.is_coinfection),
      secondary: (result.secondary_diseases || []).map((s) => s.name_vi || s.class),
      lesions: result.lesion_count ?? (result.detections || []).length,
      simulated: Boolean(result.simulated),
      synced_to_supabase: Boolean(result.synced_to_supabase),
      thumb
    });
  }

  // ------------------------------------------------------------------
  // Model switch
  // ------------------------------------------------------------------
  document.querySelectorAll('[data-model]').forEach((btn) => {
    btn.addEventListener('click', () => {
      const model = btn.dataset.model;
      if (model === state.model) return;
      state.model = model;
      document.querySelectorAll('[data-model]').forEach((b) => b.setAttribute('aria-pressed', String(b === btn)));
      const m = MODELS[model];
      $('modelTag').textContent = m.label;
      $('specClasses').textContent = m.classes;
      $('specMap').textContent = m.map;
      $('specRecall').textContent = m.recall;
      if (state.src) runDiagnosis(state.src, { save: false });
    });
  });

  // ------------------------------------------------------------------
  // Nguồn ảnh: mẫu, file, camera
  // ------------------------------------------------------------------
  const sampleButtons = [...document.querySelectorAll('.sample')];
  const markSample = (btn) => sampleButtons.forEach((b) => b.setAttribute('aria-pressed', String(b === btn)));

  sampleButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      markSample(btn);
      runDiagnosis(btn.dataset.sample);
    });
  });

  const cameraDialog = $('cameraDialog');
  const camera = new LeafCameraManager({
    videoElement: $('cameraVideo'),
    onImageCaptured: (base64) => {
      markSample(null);
      setStep(1);
      runDiagnosis(base64);
    }
  });
  camera.initDropZone($('dropZone'), $('fileInput'));

  $('btnPickFile').addEventListener('click', () => $('fileInput').click());
  $('btnRescan').addEventListener('click', () => {
    if (state.src) runDiagnosis(state.src);
    else toast('Chọn một ảnh lá trước khi quét.');
  });

  $('btnOpenCamera').addEventListener('click', async () => {
    cameraDialog.showModal();
    try {
      await camera.startCamera();
    } catch (err) {
      cameraDialog.close();
      toast(err.name === 'NotAllowedError'
        ? 'Bạn chưa cho phép dùng camera. Hãy bật quyền camera trong trình duyệt.'
        : 'Không mở được camera. Hãy chọn ảnh từ máy thay thế.');
    }
  });
  $('btnFlipCamera').addEventListener('click', () => camera.toggleFacingMode().catch(() => toast('Thiết bị chỉ có một camera.')));
  $('btnSnapPhoto').addEventListener('click', () => {
    camera.captureSnapshot();
    cameraDialog.close();
  });
  cameraDialog.querySelectorAll('[data-close]').forEach((b) => b.addEventListener('click', () => cameraDialog.close()));
  cameraDialog.addEventListener('close', () => camera.stopCamera());

  $('btnProtocol').addEventListener('click', () => setStep(5));

  const btnModeBox = $('btnModeBox');
  const btnModeHeatmap = $('btnModeHeatmap');
  if (btnModeBox) btnModeBox.addEventListener('click', () => setViewMode('box'));
  if (btnModeHeatmap) btnModeHeatmap.addEventListener('click', () => setViewMode('heatmap'));

  // Vẽ lại canvas khi đổi kích thước (gom bằng requestAnimationFrame)
  let raf = 0;
  window.addEventListener('resize', () => {
    cancelAnimationFrame(raf);
    raf = requestAnimationFrame(() => { renderer.resizeCanvas(); renderer.render(); });
  });

  // ------------------------------------------------------------------
  // Khởi tạo: chạy thử ảnh mẫu đầu tiên (không lưu lịch sử)
  // ------------------------------------------------------------------
  setStep(1);
  renderer.render();
  markSample(sampleButtons[0]);
  runDiagnosis(sampleButtons[0].dataset.sample, { save: false });
})();

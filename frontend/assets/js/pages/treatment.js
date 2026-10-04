/**
 * LEAF_AI — Phác đồ điều trị (treatment.html?id=Anthracnose&p=91)
 * Luồng: nhận bệnh từ trang chẩn đoán → người dùng đánh giá mức độ, giai đoạn, diện tích
 * → lập lịch (máy chủ /treatment/plan, dự phòng trên máy) → đánh dấu tiến độ, lưu, xuất lịch.
 */
(function () {
  'use strict';
  const { escapeHtml, toast, params, diseases } = window.Leaf;
  const $ = (id) => document.getElementById(id);
  const api = new LeafApiService();

  const STORE_KEY = 'leaf_treatments';
  const TYPE = {
    cultural: { label: 'Canh tác', icon: 'bi-scissors' },
    biological: { label: 'Sinh học', icon: 'bi-bug' },
    monitor: { label: 'Kiểm tra', icon: 'bi-search' },
    chemical: { label: 'Hóa học', icon: 'bi-droplet-half' },
    evaluate: { label: 'Đánh giá', icon: 'bi-clipboard-check' }
  };
  const SEV_CLASS = { nhe: 'sev-low', trung_binh: 'sev-mid', nang: 'sev-high' };

  const state = { kb: null, plan: null, opts: null, done: new Set(), key: null, busy: false };

  // ------------------------------------------------------------------
  // Lưu trữ phác đồ đang theo dõi (localStorage)
  // ------------------------------------------------------------------
  const store = {
    all() { try { return JSON.parse(localStorage.getItem(STORE_KEY) || '[]'); } catch { return []; } },
    save(list) { try { localStorage.setItem(STORE_KEY, JSON.stringify(list.slice(0, 20))); } catch { /* đầy bộ nhớ */ } },
    get(key) { return store.all().find((x) => x.key === key) || null; },
    upsert(item) { store.save([item, ...store.all().filter((x) => x.key !== item.key)]); },
    remove(key) { store.save(store.all().filter((x) => x.key !== key)); }
  };

  const fmt = (iso) => { const [, m, d] = iso.split('-'); return `${d}/${m}`; };
  const fmtFull = (iso) => { const [y, m, d] = iso.split('-'); return `${d}/${m}/${y}`; };
  const planKey = (p) => `${p.disease.id}_${p.start_date}`;

  // ------------------------------------------------------------------
  // Form
  // ------------------------------------------------------------------
  function fillForm(kb) {
    $('fDisease').innerHTML = Object.entries(kb.diseases)
      .map(([id, d]) => `<option value="${id}">${escapeHtml(d.name_vi)} (${escapeHtml(d.kind.toLowerCase())})</option>`).join('');
    $('fStage').innerHTML = Object.entries(kb.growth_stages)
      .map(([id, label]) => `<option value="${id}">${escapeHtml(label)}</option>`).join('');
    $('fStage').value = 'loc_non';
    $('fStart').value = window.LeafTreatment.todayIso();
  }

  function readForm() {
    const harvest = $('fHarvest').value.trim();
    return {
      disease: $('fDisease').value,
      severity: (document.querySelector('input[name="sev"]:checked') || {}).value || 'trung_binh',
      growth_stage: $('fStage').value,
      area_m2: Math.max(1, Number($('fArea').value) || 1000),
      start_date: $('fStart').value || window.LeafTreatment.todayIso(),
      days_to_harvest: harvest === '' ? null : Math.max(0, Math.round(Number(harvest)))
    };
  }

  function writeForm(o) {
    if (o.disease) $('fDisease').value = window.LeafTreatment.resolveDisease(state.kb, o.disease) || $('fDisease').value;
    const sev = document.querySelector(`input[name="sev"][value="${o.severity}"]`);
    if (sev) sev.checked = true;
    if (o.growth_stage) $('fStage').value = o.growth_stage;
    if (o.area_m2) $('fArea').value = o.area_m2;
    if (o.start_date) $('fStart').value = o.start_date;
    $('fHarvest').value = o.days_to_harvest ?? '';
    updateSevHint();
  }

  function updateSevHint() {
    const sev = (document.querySelector('input[name="sev"]:checked') || {}).value;
    const lvl = state.kb && state.kb.severity_levels[sev];
    $('sevHint').textContent = lvl ? lvl.criteria + ' Mức độ do bạn đánh giá trên vườn, không phải độ tin cậy của AI.' : '';
  }

  // ------------------------------------------------------------------
  // Hiển thị phác đồ
  // ------------------------------------------------------------------
  function renderPlan(plan) {
    const d = plan.disease;
    $('planBox').hidden = false;
    $('planTitle').textContent = `Điều trị ${d.name_vi.toLowerCase()}`;
    $('planLatin').innerHTML = `<em>${escapeHtml(d.pathogen)}</em> · ${escapeHtml(d.kind)}`;
    $('planTags').innerHTML = `
      <span class="sev ${SEV_CLASS[plan.severity.key]}">Mức độ: ${escapeHtml(plan.severity.label)}</span>
      <span class="tag">${escapeHtml(plan.growth_stage.label)}</span>
      <span class="tag">${Number(plan.area_m2).toLocaleString('vi-VN')} m²</span>`;
    const server = plan.generated_by === 'server';
    $('planSource').innerHTML = server
      ? '<i class="bi bi-cloud-check"></i>Lập bởi máy chủ LEAF_AI'
      : '<i class="bi bi-wifi-off"></i>Lập trên máy (ngoại tuyến)';
    $('planSource').classList.toggle('tag-warn', !server);

    const chem = plan.steps.filter((s) => s.type === 'chemical' && !s.blocked);
    $('factDuration').textContent = `${plan.duration_days} ngày (${fmt(plan.start_date)}–${fmt(plan.end_date)})`;
    $('factSteps').textContent = String(plan.steps.length);
    $('factChem').textContent = chem.length ? `Tối đa ${chem.length}` : 'Không dùng';
    $('factSpray').textContent = `≈ ${plan.spray.liquid_l.toLocaleString('vi-VN')} L · ${plan.spray.tanks} bình`;

    const notes = [...plan.notes];
    $('planNotes').hidden = notes.length === 0;
    $('planNotesText').textContent = notes.join(' ');

    const today = window.LeafTreatment.todayIso();
    $('planSteps').innerHTML = plan.steps.map((s, i) => {
      const t = TYPE[s.type] || TYPE.monitor;
      const cls = ['step-' + s.type];
      if (s.conditional) cls.push('is-conditional');
      if (s.blocked) cls.push('is-blocked');
      if (s.date === today) cls.push('is-today');
      if (s.date < today && !state.done.has(i) && !s.blocked) cls.push('is-overdue');
      const products = s.products.length
        ? `<p class="plan-products"><i class="bi bi-capsule"></i>Hoạt chất gợi ý: ${s.products.map((p) => `<b>${escapeHtml(p.active)}</b> <span class="muted">(${escapeHtml(p.group)})</span>`).join(', ')}</p>`
        : '';
      const warns = s.warnings.map((w) => `<p class="plan-warn"><i class="bi bi-exclamation-triangle"></i>${escapeHtml(w)}</p>`).join('');
      return `<li class="${cls.join(' ')}" data-i="${i}">
        <div class="plan-date"><b>Ngày ${s.day}</b><span>${fmt(s.date)}</span></div>
        <div class="plan-body">
          <div class="plan-step-head">
            <span class="plan-type"><i class="bi ${t.icon}"></i>${t.label}</span>
            <h3>${escapeHtml(s.title)}</h3>
            ${s.blocked ? '<span class="tag tag-warn">Không áp dụng</span>' : ''}
            ${s.conditional && !s.blocked ? '<span class="tag tag-warn">Có điều kiện</span>' : ''}
          </div>
          <ul>${s.actions.map((a) => `<li>${escapeHtml(a)}</li>`).join('')}</ul>
          ${products}${warns}
        </div>
        <label class="plan-check"><input type="checkbox" ${state.done.has(i) ? 'checked' : ''} ${s.blocked ? 'disabled' : ''} aria-label="Đánh dấu đã làm: ${escapeHtml(s.title)}"><span>Đã làm</span></label>
      </li>`;
    }).join('');

    $('planRefs').textContent = `Nguồn: ${plan.source}`;
    $('asideSuccess').textContent = plan.success;
    $('asideRules').innerHTML = plan.rules.map((r) => `<li>${escapeHtml(r)}</li>`).join('');
    updateProgress();
  }

  function updateProgress() {
    if (!state.plan) return;
    const usable = state.plan.steps.filter((s) => !s.blocked).length;
    const done = [...state.done].filter((i) => !state.plan.steps[i].blocked).length;
    $('progressText').textContent = `${done}/${usable} bước`;
    $('progressBar').style.width = usable ? `${Math.round((done / usable) * 100)}%` : '0%';
  }

  function renderSaved() {
    const list = store.all();
    $('savedEmpty').hidden = list.length > 0;
    $('savedPlans').innerHTML = list.map((x) => {
      const pct = x.total ? Math.round((x.done.length / x.total) * 100) : 0;
      return `<li><a href="treatment.html?plan=${encodeURIComponent(x.key)}"${x.key === state.key ? ' aria-current="page"' : ''}>
        <span class="dot" style="--dot:${escapeHtml(x.color || '#1e7a4c')}"></span>
        <span class="saved-name">${escapeHtml(x.title)}<small>${fmtFull(x.start)} · ${pct}% hoàn thành</small></span>
      </a></li>`;
    }).join('');
  }

  // ------------------------------------------------------------------
  // Hành động
  // ------------------------------------------------------------------
  async function build(opts, { done = [] } = {}) {
    if (state.busy) return;
    state.busy = true;
    $('btnBuild').disabled = true;
    $('btnBuild').innerHTML = '<i class="bi bi-hourglass-split"></i>Đang lập phác đồ…';
    try {
      const plan = await api.getTreatmentPlan(opts);
      state.plan = plan;
      state.opts = opts;
      state.key = planKey(plan);
      const saved = store.get(state.key);
      state.done = new Set(done.length ? done : saved ? saved.done : []);
      renderPlan(plan);
      renderSaved();
    } catch (err) {
      toast(err.message || 'Không lập được phác đồ, hãy thử lại.');
    } finally {
      state.busy = false;
      $('btnBuild').disabled = false;
      $('btnBuild').innerHTML = '<i class="bi bi-clipboard2-pulse"></i>Lập lại phác đồ';
    }
  }

  function saveCurrent(silent) {
    if (!state.plan) return;
    const info = diseases.find(state.plan.disease.class) || {};
    store.upsert({
      key: state.key,
      opts: state.opts,
      title: `${state.plan.disease.name_vi} · ${state.plan.severity.label.toLowerCase()}`,
      start: state.plan.start_date,
      color: info.color,
      done: [...state.done],
      total: state.plan.steps.filter((s) => !s.blocked).length,
      savedAt: new Date().toISOString()
    });
    renderSaved();
    if (!silent) toast('Đã lưu phác đồ để theo dõi');
  }

  /** Xuất lịch .ics: mỗi bước là một sự kiện cả ngày, có nhắc lúc 6:30 sáng */
  function exportIcs() {
    const p = state.plan;
    if (!p) return;
    const esc = (s) => String(s).replace(/\\/g, '\\\\').replace(/\n/g, '\\n').replace(/[,;]/g, (c) => `\\${c}`);
    const ymd = (iso) => iso.replace(/-/g, '');
    const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d+Z$/, 'Z');
    const events = p.steps.filter((s) => !s.blocked).map((s, i) => {
      const lines = [...s.actions, ...s.products.map((x) => `Hoạt chất gợi ý: ${x.active} (${x.group})`), ...s.warnings];
      return [
        'BEGIN:VEVENT',
        `UID:${state.key}-${i}@leaf-ai`,
        `DTSTAMP:${stamp}`,
        `DTSTART;VALUE=DATE:${ymd(s.date)}`,
        `DTEND;VALUE=DATE:${ymd(window.LeafTreatment.addDays(s.date, 1))}`,
        `SUMMARY:${esc(`LEAF_AI – ${p.disease.name_vi}: ${s.title}`)}`,
        `DESCRIPTION:${esc(lines.join('\n'))}`,
        'BEGIN:VALARM', 'ACTION:DISPLAY', `DESCRIPTION:${esc(s.title)}`, 'TRIGGER:PT6H30M', 'END:VALARM',
        'END:VEVENT'
      ].join('\r\n');
    });
    const ics = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//LEAF_AI//Phac do dieu tri//VI', 'CALSCALE:GREGORIAN', ...events, 'END:VCALENDAR'].join('\r\n');
    const url = URL.createObjectURL(new Blob([ics], { type: 'text/calendar;charset=utf-8' }));
    const a = Object.assign(document.createElement('a'), { href: url, download: `leaf-ai-phac-do-${state.key}.ics` });
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast('Đã tạo tệp lịch, mở tệp để thêm vào lịch điện thoại');
  }

  $('planForm').addEventListener('submit', (e) => {
    e.preventDefault();
    build(readForm());
  });
  $('fSeverity').addEventListener('change', updateSevHint);

  $('planSteps').addEventListener('change', (e) => {
    const box = e.target.closest('input[type="checkbox"]');
    if (!box) return;
    const i = Number(box.closest('li[data-i]').dataset.i);
    if (box.checked) state.done.add(i); else state.done.delete(i);
    box.closest('li[data-i]').classList.remove('is-overdue');
    updateProgress();
    const first = !store.get(state.key);
    saveCurrent(true);
    if (first) toast('Đã lưu phác đồ để theo dõi tiến độ');
  });

  $('btnSave').addEventListener('click', () => saveCurrent(false));
  $('btnIcs').addEventListener('click', exportIcs);
  $('btnPrint').addEventListener('click', () => window.print());

  // ------------------------------------------------------------------
  // Khởi tạo
  // ------------------------------------------------------------------
  (async function init() {
    try {
      state.kb = await window.LeafTreatment.loadKB();
    } catch {
      toast('Không tải được kho phác đồ. Kiểm tra kết nối rồi tải lại trang.');
      return;
    }
    fillForm(state.kb);
    renderSaved();

    const savedKey = params.get('plan');
    const saved = savedKey ? store.get(savedKey) : null;
    if (saved) {
      writeForm(saved.opts);
      await build(saved.opts, { done: saved.done });
      return;
    }

    const fromScan = params.get('id');
    if (fromScan) {
      $('fromScanTag').hidden = false;
      const prob = params.get('p');
      if (prob) $('fromScanTag').innerHTML = `<i class="bi bi-camera"></i>Từ kết quả chẩn đoán (${Math.round(Number(prob))}%)`;
    }
    writeForm({ disease: fromScan || 'anthracnose', severity: params.get('sev') || 'trung_binh' });
    await build(readForm());
  })();
})();

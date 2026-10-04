/**
 * LEAF_AI — Nhật ký đồng ruộng (history.html)
 * Nguồn dữ liệu: backend (nếu chạy) ghép với ảnh thu nhỏ lưu trên máy; ngược lại dùng localStorage.
 */
(function () {
  'use strict';
  const { diseases, sevBadge, escapeHtml, history, toast, confirm } = window.Leaf;
  const $ = (id) => document.getElementById(id);
  const api = new LeafApiService();

  let records = [];
  let filter = 'all';

  // ------------------------------------------------------------------
  // Chuẩn hoá bản ghi (backend và local có cấu trúc khác nhau)
  // ------------------------------------------------------------------
  function parseTime(t) {
    if (!t) return null;
    const iso = new Date(t);
    if (!Number.isNaN(iso.getTime()) && /\d{4}-\d{2}-\d{2}/.test(t)) return iso;
    const m = String(t).match(/(\d{1,2})\/(\d{1,2})\/(\d{4})[, ]*(\d{1,2}):(\d{2})(?::(\d{2}))?/); // dd/mm/yyyy, hh:mm:ss
    if (m) return new Date(+m[3], +m[2] - 1, +m[1], +m[4], +m[5], +(m[6] || 0));
    const m2 = String(t).match(/(\d{1,2}):(\d{2}):?(\d{2})?\s+(\d{1,2})\/(\d{1,2})\/(\d{4})/); // hh:mm:ss dd/mm/yyyy
    if (m2) return new Date(+m2[6], +m2[5] - 1, +m2[4], +m2[1], +m2[2], +(m2[3] || 0));
    return null;
  }

  function normalize(r, thumbs = {}) {
    const name = r.primary_disease_vi || r.primary_disease || 'Không rõ';
    const healthy = r.class === 'Healthy' || /khỏe/i.test(name);
    const info = healthy ? null : diseases.find(r.class) || diseases.find(r.primary_disease) || diseases.find(name);
    return {
      id: r.id,
      name: info ? info.name_vi : name,
      info,
      healthy,
      prob: Math.round(r.probability ?? r.confidence ?? 0),
      severity: healthy ? 'Khỏe' : r.severity,
      model: String(r.model || r.model_version || 'ResNet-18'),
      time: parseTime(r.timestamp),
      rawTime: r.timestamp || '',
      coinf: Boolean(r.is_coinfection),
      secondary: r.secondary || (r.secondary_diseases || []).map((s) => s.name_vi || s.class || s),
      lesions: r.lesions,
      thumb: r.thumb || thumbs[String(r.id)] || '',
      simulated: Boolean(r.simulated),
      synced: Boolean(r.synced_to_supabase)
    };
  }

  const fmtTime = (d, raw) => (d ? d.toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit', year: 'numeric' }) : raw);

  function relative(d) {
    if (!d) return '—';
    const mins = Math.round((Date.now() - d.getTime()) / 60000);
    if (mins < 1) return 'Vừa xong';
    if (mins < 60) return `${mins} phút trước`;
    const hrs = Math.round(mins / 60);
    if (hrs < 24) return `${hrs} giờ trước`;
    const days = Math.round(hrs / 24);
    return days < 30 ? `${days} ngày trước` : fmtTime(d);
  }

  // ------------------------------------------------------------------
  // Render
  // ------------------------------------------------------------------
  function renderSummary() {
    const sick = records.filter((r) => !r.healthy);
    $('sTotal').textContent = records.length;
    $('sSick').innerHTML = `${sick.length}<small>${records.filter((r) => r.coinf).length} lần đồng nhiễm</small>`;

    const counts = {};
    sick.forEach((r) => (counts[r.name] = (counts[r.name] || 0) + 1));
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
    $('sTop').innerHTML = top ? `${escapeHtml(top[0].split(' (')[0])}<small>${top[1]} lần</small>` : '—';

    const latest = records.map((r) => r.time).filter(Boolean).sort((a, b) => b - a)[0];
    $('sLast').textContent = relative(latest);
  }

  function renderList() {
    const list = records.filter((r) =>
      filter === 'sick' ? !r.healthy : filter === 'coinf' ? r.coinf : filter === 'healthy' ? r.healthy : true);

    if (records.length === 0) {
      $('records').innerHTML = `<li class="panel empty">
        <i class="bi bi-journal-plus"></i>
        <h3>Chưa có lần quét nào</h3>
        <p class="small">Kết quả mỗi lần chẩn đoán sẽ tự động lưu ở đây.</p>
        <a class="btn btn-primary" href="scan.html"><i class="bi bi-camera"></i>Quét lá đầu tiên</a>
      </li>`;
      return;
    }
    if (list.length === 0) {
      $('records').innerHTML = `<li class="panel empty"><i class="bi bi-funnel"></i><h3>Không có bản ghi phù hợp bộ lọc</h3></li>`;
      return;
    }

    $('records').innerHTML = list.map((r) => `
      <li class="record">
        ${r.thumb ? `<img class="ph" src="${r.thumb}" alt="">` : `<span class="ph"><i class="bi ${r.healthy ? 'bi-flower1' : 'bi-virus'}"></i></span>`}
        <div style="min-width:0">
          <h3>
            ${r.info ? `<a href="disease.html?id=${r.info.id}">${escapeHtml(r.name)}</a>` : escapeHtml(r.name)}
            ${r.healthy ? '<span class="sev sev-low">Khỏe</span>' : sevBadge(r.severity)}
          </h3>
          <div class="meta">
            <span><i class="bi bi-clock"></i> ${escapeHtml(fmtTime(r.time, r.rawTime))}</span>
            ${r.healthy ? '' : `<span>Độ tin cậy ${r.prob}%</span>`}
            <span class="tag">${escapeHtml(r.model)}</span>
            ${r.coinf ? `<span class="tag tag-warn">Đồng nhiễm${r.secondary.length ? ': ' + escapeHtml(r.secondary.join(', ')) : ''}</span>` : ''}
            ${r.synced ? '<span class="tag"><i class="bi bi-cloud-check"></i>Đã đồng bộ</span>' : ''}
            ${r.simulated ? '<span>Mô phỏng</span>' : ''}
          </div>
        </div>
        <button class="btn btn-ghost btn-icon" type="button" data-delete="${escapeHtml(r.id)}" aria-label="Xóa bản ghi ${escapeHtml(r.name)}"><i class="bi bi-trash3"></i></button>
      </li>`).join('');
  }

  function render() {
    renderSummary();
    renderList();
    $('btnClear').disabled = records.length === 0;
    $('btnExport').disabled = records.length === 0;
  }

  // ------------------------------------------------------------------
  // Tải dữ liệu
  // ------------------------------------------------------------------
  async function load() {
    const local = history.all();
    records = local.map((r) => normalize(r));
    render();

    const server = await api.getHistory(50);
    if (Array.isArray(server)) {
      const thumbs = Object.fromEntries(local.map((r) => [String(r.id), r.thumb]));
      records = server.map((r) => normalize(r, thumbs));
      $('sourceNote').textContent = 'Đang hiển thị dữ liệu từ máy chủ';
      render();
    } else {
      $('sourceNote').textContent = local.length ? 'Lưu trên thiết bị này' : '';
    }
  }

  // ------------------------------------------------------------------
  // Sự kiện
  // ------------------------------------------------------------------
  document.querySelectorAll('[data-filter]').forEach((chip) => chip.addEventListener('click', () => {
    filter = chip.dataset.filter;
    document.querySelectorAll('[data-filter]').forEach((c) => c.setAttribute('aria-pressed', String(c === chip)));
    renderList();
  }));

  $('records').addEventListener('click', async (e) => {
    const btn = e.target.closest('[data-delete]');
    if (!btn) return;
    const id = btn.dataset.delete;
    if (!(await confirm('Bản ghi này sẽ bị xóa khỏi thiết bị và máy chủ (nếu có).', { title: 'Xóa bản ghi?', okText: 'Xóa' }))) return;
    await api.deleteHistoryRecord(id);
    history.remove(id);
    records = records.filter((r) => String(r.id) !== String(id));
    render();
    toast('Đã xóa bản ghi');
  });

  $('btnClear').addEventListener('click', async () => {
    if (!(await confirm(`Xóa toàn bộ ${records.length} bản ghi? Thao tác này không hoàn tác được.`, { title: 'Xóa toàn bộ lịch sử?', okText: 'Xóa toàn bộ' }))) return;
    await api.clearHistoryAll();
    history.clear();
    records = [];
    render();
    toast('Đã xóa toàn bộ lịch sử');
  });

  $('btnExport').addEventListener('click', () => {
    const rows = [['Thời gian', 'Bệnh chính', 'Độ tin cậy (%)', 'Mức độ', 'Mô hình', 'Đồng nhiễm', 'Bệnh phụ']];
    records.forEach((r) => rows.push([fmtTime(r.time, r.rawTime), r.name, r.healthy ? '' : r.prob, r.severity || '', r.model, r.coinf ? 'Có' : 'Không', r.secondary.join('; ')]));
    const csv = '﻿' + rows.map((row) => row.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const a = Object.assign(document.createElement('a'), { href: url, download: `leaf_ai_nhat_ky_${new Date().toISOString().slice(0, 10)}.csv` });
    a.click();
    URL.revokeObjectURL(url);
  });

  load();
})();

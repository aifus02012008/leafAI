/**
 * LEAF_AI — Thư viện bệnh (library.html)
 * Tìm kiếm + lọc tại chỗ, mỗi thẻ dẫn tới trang chi tiết disease.html?id=...
 */
(function () {
  'use strict';
  const { diseases, sevBadge, escapeHtml, params } = window.Leaf;

  const grid = document.getElementById('libGrid');
  const count = document.getElementById('libCount');
  const search = document.getElementById('libSearch');
  const chips = [...document.querySelectorAll('[data-filter]')];

  let filter = 'all';
  const all = diseases.list();

  // Chuẩn hoá để tìm kiếm không phân biệt dấu
  const norm = (s) => String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/đ/g, 'd');

  function matches(d, term) {
    if (filter === 'fungus' && d.id === 'bacterial_spot') return false;
    if (filter === 'bacteria' && d.id !== 'bacterial_spot') return false;
    if (filter === 'severe' && d.severity_default !== 'Nghiêm trọng') return false;
    if (!term) return true;
    const hay = norm([d.name_vi, d.name_en, d.pathogen, d.symptoms.stage_1, d.symptoms.stage_2, d.conditions].join(' '));
    return hay.includes(term);
  }

  function render() {
    const term = norm(search.value.trim());
    const list = all.filter((d) => matches(d, term));
    count.textContent = list.length === all.length ? `${all.length} bệnh` : `${list.length} / ${all.length} bệnh phù hợp`;

    if (list.length === 0) {
      grid.innerHTML = `<div class="empty panel" style="grid-column:1/-1">
        <i class="bi bi-search"></i>
        <h3>Không tìm thấy bệnh phù hợp</h3>
        <p class="small">Thử từ khoá ngắn hơn như “đốm”, “mốc” hoặc tên tác nhân.</p>
        <button class="btn" type="button" id="btnResetFilter">Xoá bộ lọc</button>
      </div>`;
      document.getElementById('btnResetFilter').addEventListener('click', reset);
      return;
    }

    grid.innerHTML = list.map((d) => `
      <a class="disease-card" href="disease.html?id=${d.id}">
        <div class="thumb"><img src="${d.thumb}" alt="Minh hoạ ${escapeHtml(d.name_vi)}" loading="lazy"></div>
        <div class="body">
          <div class="row">
            <div>
              <h3>${escapeHtml(d.name_vi)}</h3>
              <div class="latin">${escapeHtml(d.pathogen)}</div>
            </div>
            ${sevBadge(d.severity_default)}
          </div>
          <p class="excerpt">${escapeHtml(d.symptoms.stage_1)}</p>
          <div class="foot">
            <span>Xem triệu chứng và phác đồ</span>
            <span class="tag">${diseases.kind(d)}</span>
          </div>
        </div>
      </a>`).join('');
  }

  function reset() {
    search.value = '';
    filter = 'all';
    chips.forEach((c) => c.setAttribute('aria-pressed', String(c.dataset.filter === 'all')));
    render();
  }

  chips.forEach((chip) => chip.addEventListener('click', () => {
    filter = chip.dataset.filter;
    chips.forEach((c) => c.setAttribute('aria-pressed', String(c === chip)));
    render();
  }));
  search.addEventListener('input', render);

  if (params.get('q')) search.value = params.get('q');
  render();
})();

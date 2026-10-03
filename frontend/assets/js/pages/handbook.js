/**
 * LEAF_AI — Cẩm nang IPM (handbook.html)
 * Dựng nội dung từ LEAF_DATA.handbook, mục lục tự sáng theo vị trí cuộn.
 */
(function () {
  'use strict';
  const { escapeHtml } = window.Leaf;
  const hb = LEAF_DATA.handbook;
  const $ = (id) => document.getElementById(id);

  const PRINCIPLE_ICONS = ['bi-award', 'bi-bucket', 'bi-rulers', 'bi-droplet', 'bi-diagram-2', 'bi-scissors', 'bi-layers', 'bi-recycle'];
  const SAFE_ICONS = ['bi-capsule', 'bi-clock', 'bi-eyedropper', 'bi-wind', 'bi-calendar-check', 'bi-person-badge'];

  $('listPrinciples').innerHTML = hb.principles.map((p, i) => `
    <article class="principle">
      <h3><i class="bi ${PRINCIPLE_ICONS[i] || 'bi-check2-circle'}"></i>${escapeHtml(p.title)}</h3>
      <p>${escapeHtml(p.desc)}</p>
    </article>`).join('');

  const seqItem = (n, title, desc, cls = '') => `
    <li class="${cls}"><b>${n}</b><div><h3>${escapeHtml(title)}</h3><p>${escapeHtml(desc)}</p></div></li>`;

  $('listInspection').innerHTML = hb.inspection.map((s) => seqItem(s.step, s.title, s.desc)).join('');
  $('listIpm').innerHTML = hb.ipm.map((s) => {
    const cls = /LEAF_AI/.test(s.desc) || /nhận diện/i.test(s.title) ? 'is-ai' : /hóa học/i.test(s.title) ? 'is-chem' : '';
    return seqItem(s.step, s.title, s.desc, cls);
  }).join('');

  $('listSafe').innerHTML = hb.safe_pesticide.map((r, i) => `
    <article class="rule">
      <i class="bi ${SAFE_ICONS[i] || 'bi-shield-check'}"></i>
      <h3>${escapeHtml(r.rule.replace(/^\d+\.\s*/, ''))}</h3>
      <p>${escapeHtml(r.desc)}</p>
    </article>`).join('');

  // Mục lục: đánh dấu mục đang xem
  const links = [...document.querySelectorAll('#toc a')];
  const setActive = (id) => links.forEach((a) => {
    const on = a.getAttribute('href') === `#${id}`;
    a.classList.toggle('is-active', on);
    if (on && window.matchMedia('(max-width: 960px)').matches) {
      a.scrollIntoView({ block: 'nearest', inline: 'center', behavior: 'smooth' });
    }
  });
  const io = new IntersectionObserver((entries) => {
    const visible = entries.filter((e) => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
    if (visible) setActive(visible.target.id);
  }, { rootMargin: '-30% 0px -60% 0px' });
  document.querySelectorAll('.hb-section').forEach((s) => io.observe(s));
  setActive((location.hash || '#nguyen-tac').slice(1));
})();

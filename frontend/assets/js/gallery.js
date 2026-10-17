/**
 * LEAF_AI — Lightbox xem ảnh lớn cho mọi <img data-lightbox>.
 * Dùng <dialog> gốc của trình duyệt (Esc để đóng, focus tự quản lý), event delegation, không phụ thuộc thư viện.
 */
(function () {
  'use strict';

  const imgs = () => Array.from(document.querySelectorAll('img[data-lightbox]'));
  if (!imgs().length || typeof HTMLDialogElement === 'undefined') return;

  const dlg = document.createElement('dialog');
  dlg.className = 'lightbox';
  dlg.setAttribute('aria-label', 'Xem ảnh lớn');
  dlg.innerHTML = `
    <figure class="lightbox-figure">
      <img alt="" decoding="async">
      <figcaption></figcaption>
    </figure>
    <button type="button" class="lightbox-btn lightbox-close" aria-label="Đóng"><i class="bi bi-x-lg"></i></button>
    <button type="button" class="lightbox-btn lightbox-prev" aria-label="Ảnh trước"><i class="bi bi-chevron-left"></i></button>
    <button type="button" class="lightbox-btn lightbox-next" aria-label="Ảnh sau"><i class="bi bi-chevron-right"></i></button>`;
  document.body.appendChild(dlg);

  const big = dlg.querySelector('img');
  const cap = dlg.querySelector('figcaption');
  let list = [];
  let index = 0;

  const captionOf = (img) => img.closest('figure')?.querySelector('figcaption')?.textContent.trim() || img.alt || '';

  function show(i) {
    index = (i + list.length) % list.length;
    const img = list[index];
    big.src = img.currentSrc || img.src;
    big.alt = img.alt;
    cap.textContent = captionOf(img);
  }

  document.addEventListener('click', (e) => {
    const img = e.target.closest('img[data-lightbox]');
    if (!img) return;
    e.preventDefault();
    list = imgs();
    show(list.indexOf(img));
    if (!dlg.open) dlg.showModal();
  });

  dlg.querySelector('.lightbox-close').addEventListener('click', () => dlg.close());
  dlg.querySelector('.lightbox-prev').addEventListener('click', () => show(index - 1));
  dlg.querySelector('.lightbox-next').addEventListener('click', () => show(index + 1));
  // Bấm vào nền tối để đóng
  dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
  dlg.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowLeft') show(index - 1);
    if (e.key === 'ArrowRight') show(index + 1);
  });

  // Ảnh có thể bấm được: thêm role/tabindex để dùng bàn phím
  imgs().forEach((img) => {
    img.tabIndex = 0;
    img.setAttribute('role', 'button');
    img.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); img.click(); }
    });
  });
})();

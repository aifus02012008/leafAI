/**
 * LEAF_AI — Landing page
 * Phát lại hiệu ứng quét demo ở hero khi người dùng bấm "Xem lại".
 */
(function () {
  const btn = document.getElementById('btnReplay');
  const stage = document.getElementById('demoStage');
  if (!btn || !stage) return;

  btn.addEventListener('click', () => {
    const targets = [...stage.querySelectorAll('.demo-cam, .demo-chip, .demo-scanline'), document.querySelector('.demo-result')];
    targets.forEach((el) => {
      el.style.animation = 'none';
      void el.offsetWidth; // reflow để khởi động lại animation CSS
      el.style.animation = '';
    });
  });
})();

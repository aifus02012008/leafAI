/**
 * LEAF_AI — Màn hình đăng nhập (index.html)
 * Google / email + mật khẩu, tạo tài khoản, quên mật khẩu (Firebase Auth).
 * Đăng nhập xong → vào thẳng màn hình quét (hoặc trang người dùng định mở trước đó).
 */
(function () {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const msg = $('authMsg');

  // Chỉ chuyển tới trang nội bộ của ứng dụng (chống chuyển hướng ra ngoài)
  function nextUrl() {
    const n = new URLSearchParams(location.search).get('next') || '';
    return /^[a-z0-9_-]+\.html([?#].*)?$/i.test(n) && !/^index\.html/i.test(n) ? n : 'scan.html';
  }
  let leaving = false;
  const enterApp = () => {
    if (leaving) return;
    leaving = true;
    location.replace(nextUrl());
  };

  // Đã có phiên trên máy → vào luôn
  try {
    const saved = JSON.parse(localStorage.getItem('leaf_last_user') || 'null');
    if (saved && saved.is_authenticated) { enterApp(); return; }
  } catch { /* private mode */ }

  // Firebase khôi phục được phiên (vd quay lại sau khi đăng nhập Google bằng chuyển trang)
  window.Leaf.authReady.then((u) => {
    if (u) enterApp();
    window.LeafAuth?.onAuthStateChange((_, user) => { if (user) enterApp(); });
  });

  async function getAuth() {
    if (window.LeafAuth) return window.LeafAuth;
    await window.Leaf.authReady;
    if (window.LeafAuth) return window.LeafAuth;
    throw new Error('Chưa tải được dịch vụ đăng nhập. Kiểm tra mạng rồi thử lại.');
  }

  function showMsg(text, kind = 'error') {
    msg.textContent = text || '';
    msg.dataset.kind = kind;
    msg.hidden = !text;
  }

  function busy(btn, on, label) {
    if (!btn.dataset.label) btn.dataset.label = btn.textContent.trim();
    btn.disabled = on;
    btn.classList.toggle('is-busy', on);
    btn.textContent = on ? label : btn.dataset.label;
  }

  const validEmail = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(v).trim());

  // ---------- Chuyển tab ----------
  function switchTab(mode) {
    const login = mode === 'login';
    $('tabLogin').setAttribute('aria-selected', String(login));
    $('tabSignup').setAttribute('aria-selected', String(!login));
    $('loginForm').hidden = !login;
    $('signupForm').hidden = login;
    $('authTitle').textContent = login ? 'Đăng nhập để quét lá' : 'Tạo tài khoản nhà vườn';
    showMsg('');
    (login ? $('loginEmail') : $('signupName')).focus({ preventScroll: true });
  }
  $('tabLogin').addEventListener('click', () => switchTab('login'));
  $('tabSignup').addEventListener('click', () => switchTab('signup'));

  // ---------- Hiện / ẩn mật khẩu ----------
  document.querySelectorAll('.pass-toggle').forEach((b) => {
    b.addEventListener('click', () => {
      const input = $(b.dataset.toggle);
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      b.setAttribute('aria-label', show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');
      b.querySelector('i').className = `bi ${show ? 'bi-eye-slash' : 'bi-eye'}`;
    });
  });

  // ---------- Google ----------
  $('btnGoogle').addEventListener('click', async () => {
    const btn = $('btnGoogle');
    showMsg('');
    btn.disabled = true;
    try {
      const auth = await getAuth();
      const res = await auth.signInWithGoogle();
      if (res && res.user) enterApp();
      // res = null: trình duyệt chặn popup → đang chuyển sang trang Google, quay lại sẽ tự vào
    } catch (err) {
      showMsg(err.message || 'Đăng nhập Google chưa thành công.');
    } finally {
      btn.disabled = false;
    }
  });

  // ---------- Đăng nhập email ----------
  $('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = $('loginEmail').value.trim();
    const pass = $('loginPass').value;
    if (!validEmail(email)) { showMsg('Nhập email đúng dạng, ví dụ ten@email.com.'); $('loginEmail').focus(); return; }
    if (pass.length < 6) { showMsg('Mật khẩu có ít nhất 6 ký tự.'); $('loginPass').focus(); return; }
    const btn = $('btnLogin');
    showMsg('');
    busy(btn, true, 'Đang đăng nhập…');
    try {
      const auth = await getAuth();
      const res = await auth.signInWithEmail(email, pass);
      if (res && res.user) enterApp();
    } catch (err) {
      showMsg(err.message || 'Đăng nhập chưa thành công.');
      busy(btn, false);
    }
  });

  // ---------- Tạo tài khoản ----------
  $('signupForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = $('signupName').value.trim();
    const email = $('signupEmail').value.trim();
    const pass = $('signupPass').value;
    if (!name) { showMsg('Nhập tên nhà vườn để hiển thị trong lịch sử quét.'); $('signupName').focus(); return; }
    if (!validEmail(email)) { showMsg('Nhập email đúng dạng, ví dụ ten@email.com.'); $('signupEmail').focus(); return; }
    if (pass.length < 6) { showMsg('Mật khẩu cần ít nhất 6 ký tự.'); $('signupPass').focus(); return; }
    const btn = $('btnSignup');
    showMsg('');
    busy(btn, true, 'Đang tạo tài khoản…');
    try {
      const auth = await getAuth();
      const res = await auth.signUpWithEmail(email, pass, name);
      if (res && res.user) enterApp();
    } catch (err) {
      showMsg(err.message || 'Chưa tạo được tài khoản.');
      busy(btn, false);
    }
  });

  // ---------- Quên mật khẩu ----------
  $('btnForgot').addEventListener('click', async () => {
    const email = $('loginEmail').value.trim();
    if (!validEmail(email)) {
      showMsg('Nhập email của bạn ở ô trên, rồi bấm "Quên mật khẩu?" để nhận link đặt lại.');
      $('loginEmail').focus();
      return;
    }
    const btn = $('btnForgot');
    btn.disabled = true;
    try {
      const auth = await getAuth();
      await auth.resetPassword(email);
      showMsg(`Đã gửi link đặt lại mật khẩu tới ${email}. Kiểm tra hộp thư (cả mục Spam).`, 'ok');
    } catch (err) {
      showMsg(err.message || 'Không gửi được email đặt lại mật khẩu.');
    } finally {
      btn.disabled = false;
    }
  });
})();

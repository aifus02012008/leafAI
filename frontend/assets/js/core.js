/**
 * LEAF_AI — Core layout & helpers (dùng chung cho mọi trang)
 * - Chèn header / mobile drawer / bottom nav đồng bộ (không nhấp nháy)
 * - Chèn footer khi DOM sẵn sàng
 * - Tiện ích: tra cứu bệnh, lưu lịch sử, toast, hộp xác nhận, PWA
 *
 * Trang khai báo trang hiện tại qua <body data-page="scan">.
 * Script này phải được nạp NGAY SAU thẻ <body> (không defer).
 */
(function () {
  'use strict';

  const NAV = [
    { id: 'scan', href: 'scan.html', label: 'Chẩn đoán', icon: 'bi-camera' },
    { id: 'library', href: 'library.html', label: 'Thư viện bệnh', short: 'Thư viện', icon: 'bi-journal-text' },
    { id: 'handbook', href: 'handbook.html', label: 'Cẩm nang IPM', short: 'Cẩm nang', icon: 'bi-shield-check' },
    { id: 'history', href: 'history.html', label: 'Lịch sử', icon: 'bi-clock-history' },
    { id: 'assistant', href: 'assistant.html', label: 'Trợ lý AI', short: 'Trợ lý', icon: 'bi-chat-dots' },
    { id: 'about', href: 'about.html', label: 'Giới thiệu', icon: 'bi-info-circle' }
  ];

  const LEAF_MARK = `
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M19.5 4.5c-7.2.1-12.6 3.4-14 9.2-.5 2 .1 3.8 1.3 5 3.6-4.6 7-7.1 10.2-8.6-2.8 2.1-5.6 5-7.8 8.6 1.1.4 2.4.4 3.7 0 5.1-1.7 7-7.3 6.6-14.2Z" fill="#fff"/>
    </svg>`;

  const page = document.body.dataset.page || '';
  const isActive = (id) => (id === page ? ' aria-current="page"' : '');

  // ------------------------------------------------------------------
  // Header (chèn đồng bộ để không bị nháy layout)
  // ------------------------------------------------------------------
  const headerHtml = `
    <a class="visually-hidden" href="#main">Bỏ qua điều hướng</a>
    <header class="site-header" id="siteHeader">
      <div class="container header-inner">
        <a class="brand" href="index.html" aria-label="LEAF_AI — Trang chủ">
          <span class="brand-mark">${LEAF_MARK}</span>
          <span>
            <span class="brand-name">LEAF<span>_AI</span></span>
            <span class="brand-sub">Bác sĩ lá vải Lục Ngạn</span>
          </span>
        </a>
        <nav class="main-nav" aria-label="Điều hướng chính">
          ${NAV.map((n) => `<a href="${n.href}"${isActive(n.id)}>${n.label}</a>`).join('')}
        </nav>
        <button class="btn btn-soft btn-sm" id="btnInstallPwa" hidden><i class="bi bi-download"></i>Cài ứng dụng</button>
        <div class="auth-header" id="authHeader">
          <button class="btn btn-soft btn-sm" id="btnOpenAuth" type="button"><i class="bi bi-person"></i>Đăng nhập</button>
        </div>
        <a class="btn btn-primary header-cta" href="scan.html"><i class="bi bi-camera"></i>Quét lá ngay</a>
        <button class="btn btn-ghost btn-icon menu-toggle" id="menuToggle" aria-expanded="false" aria-controls="mobileDrawer" aria-label="Mở menu">
          <i class="bi bi-list" style="font-size:1.5rem"></i>
        </button>
      </div>
    </header>
    <nav class="mobile-drawer" id="mobileDrawer" aria-label="Menu di động">
      <div id="mobileAuthRow" style="padding:12px 16px; border-bottom:1px solid var(--line); display:flex; justify-content:space-between; align-items:center;">
        <span id="mobileAuthUser" class="small muted" style="font-weight:600;"><i class="bi bi-person-circle"></i> Chưa đăng nhập</span>
        <button class="btn btn-soft btn-sm" id="btnMobileAuth" type="button">Đăng nhập</button>
      </div>
      <a href="index.html"${isActive('home')}><i class="bi bi-house"></i>Trang chủ</a>
      ${NAV.map((n) => `<a href="${n.href}"${isActive(n.id)}><i class="bi ${n.icon}"></i>${n.label}</a>`).join('')}
    </nav>
    <nav class="bottom-nav" aria-label="Điều hướng nhanh">
      <a href="index.html"${isActive('home')}><i class="bi bi-house"></i><span>Trang chủ</span></a>
      <a href="library.html"${isActive('library') || isActive('disease')}><i class="bi bi-journal-text"></i><span>Thư viện</span></a>
      <a href="scan.html" class="fab"${isActive('scan')}><i class="bi bi-camera"></i><span>Quét lá</span></a>
      <a href="history.html"${isActive('history')}><i class="bi bi-clock-history"></i><span>Lịch sử</span></a>
      <a href="assistant.html"${isActive('assistant')}><i class="bi bi-chat-dots"></i><span>Trợ lý</span></a>
    </nav>`;
  document.body.insertAdjacentHTML('afterbegin', headerHtml);

  // ------------------------------------------------------------------
  // Footer + tương tác header (sau khi DOM sẵn sàng)
  // ------------------------------------------------------------------
  const footerHtml = `
    <footer class="site-footer">
      <div class="container footer-grid">
        <div>
          <a class="brand" href="index.html">
            <span class="brand-mark">${LEAF_MARK}</span>
            <span class="brand-name">LEAF<span>_AI</span></span>
          </a>
          <p class="footer-note">Phát hiện sớm bệnh trên lá vải thiều Lục Ngạn bằng AI, xử lý theo hướng IPM để giảm thuốc hóa học và giữ vườn vải khỏe.</p>
        </div>
        <div>
          <h4>Công cụ</h4>
          <ul>
            <li><a href="scan.html">Chẩn đoán lá</a></li>
            <li><a href="history.html">Lịch sử quét</a></li>
            <li><a href="assistant.html">Trợ lý kỹ sư AI</a></li>
          </ul>
        </div>
        <div>
          <h4>Kiến thức</h4>
          <ul>
            <li><a href="library.html">Thư viện bệnh lá vải</a></li>
            <li><a href="handbook.html">Cẩm nang IPM (FAO)</a></li>
            <li><a href="handbook.html#an-toan">An toàn thuốc BVTV</a></li>
          </ul>
        </div>
        <div>
          <h4>Dự án</h4>
          <ul>
            <li><a href="about.html">Giới thiệu</a></li>
            <li><a href="about.html#mo-hinh">Mô hình ResNet-18</a></li>
            <li><a href="about.html#nguon">Nguồn tham khảo</a></li>
          </ul>
        </div>
      </div>
      <div class="container footer-bottom">
        <span>© ${new Date().getFullYear()} LEAF_AI. Đồng hành cùng nhà nông Việt Nam.</span>
        <span>Kết quả AI mang tính tham khảo, hãy hỏi cán bộ BVTV địa phương trước khi phun thuốc.</span>
      </div>
    </footer>
    <div class="toast" id="toast" role="status" aria-live="polite"></div>
    <dialog class="sheet" id="confirmDialog">
      <form method="dialog">
        <div class="sheet-head"><h2 id="confirmTitle">Xác nhận</h2></div>
        <div class="sheet-body"><p id="confirmMessage" class="muted"></p></div>
        <div class="sheet-foot">
          <button class="btn btn-ghost" value="cancel">Hủy</button>
          <button class="btn btn-danger" value="ok" id="confirmOk">Đồng ý</button>
        </div>
      </form>
    </dialog>
    <dialog class="sheet" id="authModal" aria-labelledby="authModalTitle">
      <div class="sheet-head">
        <div class="auth-tabs" role="tablist">
          <button type="button" class="auth-tab-btn is-active" id="tabBtnLogin" role="tab" aria-selected="true">Đăng nhập</button>
          <button type="button" class="auth-tab-btn" id="tabBtnSignup" role="tab" aria-selected="false">Tạo tài khoản</button>
        </div>
        <button class="btn btn-ghost btn-icon" type="button" id="btnCloseAuth" aria-label="Đóng"><i class="bi bi-x-lg"></i></button>
      </div>
      <div class="sheet-body">
        <div class="alert alert-danger" id="authError" hidden style="margin-bottom:14px;font-size:var(--fs-xs);"></div>
        <!-- Form Đăng nhập -->
        <form id="formLogin" autocomplete="on">
          <div style="margin-bottom:14px;">
            <label for="loginUser" style="display:block;font-size:var(--fs-xs);font-weight:600;margin-bottom:6px;">Tên đăng nhập hoặc Email</label>
            <div style="position:relative;">
              <i class="bi bi-person" style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--ink-3);"></i>
              <input type="text" id="loginUser" name="username" required placeholder="nhanong hoặc email@..." style="width:100%;padding:10px 12px 10px 36px;border:1px solid var(--line);border-radius:var(--r-md);font:inherit;font-size:var(--fs-sm);box-sizing:border-box;">
            </div>
          </div>
          <div style="margin-bottom:18px;">
            <label for="loginPass" style="display:block;font-size:var(--fs-xs);font-weight:600;margin-bottom:6px;">Mật khẩu</label>
            <div style="position:relative;">
              <i class="bi bi-lock" style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--ink-3);"></i>
              <input type="password" id="loginPass" name="password" required placeholder="Nhập mật khẩu" style="width:100%;padding:10px 12px 10px 36px;border:1px solid var(--line);border-radius:var(--r-md);font:inherit;font-size:var(--fs-sm);box-sizing:border-box;">
            </div>
          </div>
          <button type="submit" class="btn btn-primary btn-block" id="btnSubmitLogin"><i class="bi bi-box-arrow-in-right"></i> Đăng nhập</button>
        </form>

        <!-- Form Đăng ký -->
        <form id="formSignup" hidden autocomplete="on">
          <div style="margin-bottom:12px;">
            <label for="regUser" style="display:block;font-size:var(--fs-xs);font-weight:600;margin-bottom:6px;">Tên tài khoản</label>
            <div style="position:relative;">
              <i class="bi bi-person-badge" style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--ink-3);"></i>
              <input type="text" id="regUser" name="username" required placeholder="nhanong123 (viết liền)" style="width:100%;padding:10px 12px 10px 36px;border:1px solid var(--line);border-radius:var(--r-md);font:inherit;font-size:var(--fs-sm);box-sizing:border-box;">
            </div>
          </div>
          <div style="margin-bottom:12px;">
            <label for="regEmail" style="display:block;font-size:var(--fs-xs);font-weight:600;margin-bottom:6px;">Địa chỉ Email</label>
            <div style="position:relative;">
              <i class="bi bi-envelope" style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--ink-3);"></i>
              <input type="email" id="regEmail" name="email" required placeholder="nhanong@example.com" style="width:100%;padding:10px 12px 10px 36px;border:1px solid var(--line);border-radius:var(--r-md);font:inherit;font-size:var(--fs-sm);box-sizing:border-box;">
            </div>
          </div>
          <div style="margin-bottom:18px;">
            <label for="regPass" style="display:block;font-size:var(--fs-xs);font-weight:600;margin-bottom:6px;">Mật khẩu</label>
            <div style="position:relative;">
              <i class="bi bi-shield-lock" style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--ink-3);"></i>
              <input type="password" id="regPass" name="password" required minlength="6" placeholder="Tối thiểu 6 ký tự" style="width:100%;padding:10px 12px 10px 36px;border:1px solid var(--line);border-radius:var(--r-md);font:inherit;font-size:var(--fs-sm);box-sizing:border-box;">
            </div>
          </div>
          <button type="submit" class="btn btn-primary btn-block" id="btnSubmitSignup"><i class="bi bi-person-plus"></i> Đăng ký tài khoản</button>
        </form>
      </div>
    </dialog>`;

  function mountFooterAndBehaviour() {
    document.body.insertAdjacentHTML('beforeend', footerHtml);

    // Viền header khi cuộn — dùng IntersectionObserver thay cho scroll listener
    const header = document.getElementById('siteHeader');
    const sentinel = document.createElement('div');
    sentinel.style.cssText = 'position:absolute;top:0;height:1px;width:1px;';
    document.body.prepend(sentinel);
    new IntersectionObserver(([e]) => header.classList.toggle('is-scrolled', !e.isIntersecting)).observe(sentinel);

    // Mobile drawer
    const toggle = document.getElementById('menuToggle');
    const drawer = document.getElementById('mobileDrawer');
    const setOpen = (open) => {
      drawer.classList.toggle('is-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.querySelector('i').className = `bi ${open ? 'bi-x-lg' : 'bi-list'}`;
    };
    toggle.addEventListener('click', () => setOpen(!drawer.classList.contains('is-open')));
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setOpen(false); });
    document.addEventListener('click', (e) => {
      if (drawer.classList.contains('is-open') && !drawer.contains(e.target) && !toggle.contains(e.target)) setOpen(false);
    });

    initPwa();
    initAuth();
  }

  // ------------------------------------------------------------------
  // Auth state & Modal management
  // ------------------------------------------------------------------
  function initAuth() {
    const authModal = document.getElementById('authModal');
    if (!authModal) return;

    const authHeader = document.getElementById('authHeader');
    const mobileAuthUser = document.getElementById('mobileAuthUser');
    const mobileAuthBtn = document.getElementById('btnMobileAuth');
    const authError = document.getElementById('authError');

    const tabBtnLogin = document.getElementById('tabBtnLogin');
    const tabBtnSignup = document.getElementById('tabBtnSignup');
    const formLogin = document.getElementById('formLogin');
    const formSignup = document.getElementById('formSignup');

    function switchTab(isLogin) {
      tabBtnLogin.classList.toggle('is-active', isLogin);
      tabBtnLogin.setAttribute('aria-selected', String(isLogin));
      tabBtnSignup.classList.toggle('is-active', !isLogin);
      tabBtnSignup.setAttribute('aria-selected', String(!isLogin));
      formLogin.hidden = !isLogin;
      formSignup.hidden = isLogin;
      if (authError) authError.hidden = true;
    }

    if (tabBtnLogin) tabBtnLogin.addEventListener('click', () => switchTab(true));
    if (tabBtnSignup) tabBtnSignup.addEventListener('click', () => switchTab(false));

    const btnClose = document.getElementById('btnCloseAuth');
    if (btnClose) btnClose.addEventListener('click', () => authModal.close());

    function updateUi(user) {
      window.Leaf.currentUser = user;
      if (user && user.is_authenticated) {
        if (authHeader) {
          authHeader.innerHTML = `
            <div class="auth-user-badge" title="Tài khoản: ${escapeHtml(user.username)}">
              <i class="bi bi-person-circle"></i>
              <span>${escapeHtml(user.username)}</span>
            </div>
            <button class="btn btn-ghost btn-sm" id="btnHeaderLogout" title="Đăng xuất" type="button">
              <i class="bi bi-box-arrow-right"></i>
            </button>`;
          const btnLogout = document.getElementById('btnHeaderLogout');
          if (btnLogout) btnLogout.addEventListener('click', handleLogout);
        }
        if (mobileAuthUser) mobileAuthUser.innerHTML = `<i class="bi bi-person-check"></i> ${escapeHtml(user.username)}`;
        if (mobileAuthBtn) {
          mobileAuthBtn.innerHTML = `<i class="bi bi-box-arrow-right"></i> Đăng xuất`;
          mobileAuthBtn.onclick = handleLogout;
        }
      } else {
        if (authHeader) {
          authHeader.innerHTML = `<button class="btn btn-soft btn-sm" id="btnOpenAuth" type="button"><i class="bi bi-person"></i>Đăng nhập</button>`;
          const btnOpen = document.getElementById('btnOpenAuth');
          if (btnOpen) btnOpen.addEventListener('click', () => { switchTab(true); authModal.showModal(); });
        }
        if (mobileAuthUser) mobileAuthUser.innerHTML = `<i class="bi bi-person-circle"></i> Chưa đăng nhập`;
        if (mobileAuthBtn) {
          mobileAuthBtn.innerHTML = `Đăng nhập`;
          mobileAuthBtn.onclick = () => { switchTab(true); authModal.showModal(); };
        }
      }
    }

    async function handleLogout() {
      const ok = await confirmDialog('Bạn có chắc muốn đăng xuất khỏi tài khoản không?', { title: 'Đăng xuất', okText: 'Đăng xuất' });
      if (!ok) return;
      try {
        if (typeof LeafApiService !== 'undefined') {
          const api = new LeafApiService();
          await api.logout();
        } else {
          await fetch('/api/auth/logout/', { method: 'POST', credentials: 'include' });
        }
      } catch (e) {
        console.warn(e);
      }
      toast('Đã đăng xuất');
      updateUi(null);
    }

    async function checkAuth() {
      try {
        let res = null;
        if (typeof LeafApiService !== 'undefined') {
          const api = new LeafApiService();
          res = await api.getCurrentUser();
        } else {
          const r = await fetch('/api/auth/user/', { credentials: 'include' });
          if (r.ok) res = await r.json();
        }
        if (res && res.authenticated && res.user) {
          updateUi(res.user);
        } else {
          updateUi(null);
        }
      } catch {
        updateUi(null);
      }
    }

    if (formLogin) {
      formLogin.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = formLogin.username.value.trim();
        const password = formLogin.password.value;
        const btn = document.getElementById('btnSubmitLogin');
        btn.disabled = true;
        authError.hidden = true;
        try {
          let res = null;
          if (typeof LeafApiService !== 'undefined') {
            const api = new LeafApiService();
            res = await api.login(username, password);
          } else {
            const r = await fetch('/api/auth/login/', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ username, password }),
              credentials: 'include'
            });
            res = await r.json();
            if (!r.ok) throw new Error(res.error || 'Đăng nhập không thành công.');
          }
          toast(`Chào mừng trở lại, ${res.user.username}!`);
          authModal.close();
          formLogin.reset();
          updateUi(res.user);
        } catch (err) {
          authError.textContent = err.message || 'Đăng nhập thất bại.';
          authError.hidden = false;
        } finally {
          btn.disabled = false;
        }
      });
    }

    if (formSignup) {
      formSignup.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = formSignup.username.value.trim();
        const email = formSignup.email.value.trim();
        const password = formSignup.password.value;
        const btn = document.getElementById('btnSubmitSignup');
        btn.disabled = true;
        authError.hidden = true;
        try {
          let res = null;
          if (typeof LeafApiService !== 'undefined') {
            const api = new LeafApiService();
            res = await api.signup(username, email, password);
          } else {
            const r = await fetch('/api/auth/signup/', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ username, email, password }),
              credentials: 'include'
            });
            res = await r.json();
            if (!r.ok) throw new Error(res.error || 'Đăng ký không thành công.');
          }
          toast(`Đăng ký thành công! Chào bạn, ${res.user.username}!`);
          authModal.close();
          formSignup.reset();
          updateUi(res.user);
        } catch (err) {
          authError.textContent = err.message || 'Đăng ký thất bại.';
          authError.hidden = false;
        } finally {
          btn.disabled = false;
        }
      });
    }

    checkAuth();
  }


  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountFooterAndBehaviour);
  } else {
    mountFooterAndBehaviour();
  }

  // ------------------------------------------------------------------
  // PWA
  // ------------------------------------------------------------------
  function initPwa() {
    if ('serviceWorker' in navigator && location.protocol !== 'file:') {
      navigator.serviceWorker.register('sw.js').catch((err) => console.info('[LEAF_AI] SW không đăng ký được:', err));
    }
    let deferred = null;
    const btn = document.getElementById('btnInstallPwa');
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferred = e;
      btn.hidden = false;
    });
    btn.addEventListener('click', async () => {
      if (!deferred) return;
      deferred.prompt();
      await deferred.userChoice;
      deferred = null;
      btn.hidden = true;
    });
  }

  // ------------------------------------------------------------------
  // Helpers
  // ------------------------------------------------------------------
  const escapeHtml = (s) =>
    String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  const sevClass = (sev) => (sev === 'Nghiêm trọng' ? 'sev-high' : sev === 'Trung bình' ? 'sev-mid' : 'sev-low');
  const sevBadge = (sev) => `<span class="sev ${sevClass(sev)}">${escapeHtml(sev || 'Chưa rõ')}</span>`;

  const diseases = {
    list: () => (typeof LEAF_DATA !== 'undefined' ? Object.values(LEAF_DATA.diseases) : []),
    /** Nhận id ('anthracnose'), tên lớp mô hình ('Anthracnose', 'Leaf_mites'…) hoặc tên tiếng Việt */
    find(key) {
      if (!key) return null;
      const k = String(key).trim().toLowerCase().replace(/[\s-]+/g, '_');
      const plain = k.replace(/_/g, ' ');
      return diseases.list().find((d) => d.id === k
        || d.name_en.toLowerCase() === plain
        || d.name_vi.toLowerCase() === plain
        || (d.aliases || []).includes(k)) || null;
    },
    /** Nhãn "lá khỏe" của mô hình */
    isHealthy(key) {
      const k = String(key || '').trim().toLowerCase().replace(/[\s-]+/g, '_');
      const list = (typeof LEAF_DATA !== 'undefined' && LEAF_DATA.healthy_aliases) || ['healthy'];
      return list.includes(k);
    },
    /** Nhóm tác nhân: nấm, nấm noãn, tảo hay nhện hại */
    kind: (d) => d.kind || 'Nấm',
    /** Mô hình nhận diện được bệnh này */
    models: () => 'ResNet-18',
    url: (key) => {
      const d = diseases.find(key);
      return d ? `disease.html?id=${d.id}` : 'library.html';
    }
  };

  // Lịch sử quét (localStorage, đồng bộ backend khi có)
  const HISTORY_KEY = 'leaf_history';
  const history = {
    all() {
      try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); } catch { return []; }
    },
    save(list) {
      try {
        localStorage.setItem(HISTORY_KEY, JSON.stringify(list.slice(0, 30)));
      } catch (err) {
        // Hết dung lượng: bỏ ảnh thu nhỏ của các bản ghi cũ rồi thử lại
        const slim = list.slice(0, 30).map((r, i) => (i < 10 ? r : { ...r, thumb: '' }));
        try { localStorage.setItem(HISTORY_KEY, JSON.stringify(slim)); } catch { console.warn('[LEAF_AI] Không lưu được lịch sử', err); }
      }
    },
    add(record) {
      const list = history.all();
      list.unshift(record);
      history.save(list);
    },
    remove(id) { history.save(history.all().filter((r) => String(r.id) !== String(id))); },
    clear() { try { localStorage.removeItem(HISTORY_KEY); } catch { /* ignore */ } }
  };

  let toastTimer = 0;
  function toast(message) {
    const el = document.getElementById('toast');
    if (!el) return;
    el.textContent = message;
    el.classList.add('is-show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('is-show'), 2600);
  }

  /** Hộp xác nhận không chặn luồng (thay cho window.confirm) */
  function confirmDialog(message, { title = 'Xác nhận', okText = 'Đồng ý' } = {}) {
    const dlg = document.getElementById('confirmDialog');
    if (!dlg || typeof dlg.showModal !== 'function') return Promise.resolve(window.confirm(message));
    document.getElementById('confirmTitle').textContent = title;
    document.getElementById('confirmMessage').textContent = message;
    document.getElementById('confirmOk').textContent = okText;
    dlg.returnValue = '';
    dlg.showModal();
    return new Promise((resolve) => dlg.addEventListener('close', () => resolve(dlg.returnValue === 'ok'), { once: true }));
  }

  /** Tạo ảnh thu nhỏ (data URL) để lưu kèm lịch sử */
  function makeThumb(src, maxW = 160) {
    return new Promise((resolve) => {
      if (!src) return resolve('');
      const img = new Image();
      img.onload = () => {
        const r = Math.min(1, maxW / img.naturalWidth);
        const c = document.createElement('canvas');
        c.width = Math.round(img.naturalWidth * r);
        c.height = Math.round(img.naturalHeight * r);
        c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
        try { resolve(c.toDataURL('image/jpeg', 0.7)); } catch { resolve(''); }
      };
      img.onerror = () => resolve('');
      img.src = src;
    });
  }

  const params = new URLSearchParams(location.search);

  window.Leaf = { NAV, page, params, escapeHtml, sevClass, sevBadge, diseases, history, toast, confirm: confirmDialog, makeThumb };
})();

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
    { id: 'library', href: 'library.html', label: 'Thư viện bệnh', icon: 'bi-journal-text' },
    { id: 'history', href: 'history.html', label: 'Lịch sử', icon: 'bi-clock-history' },
    { id: 'handbook', href: 'handbook.html', label: 'Cẩm nang', icon: 'bi-shield-check' }
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
        <a class="brand" href="index.html" aria-label="LEAF_AI — Vải Lục Ngạn">
          <span class="brand-mark">${LEAF_MARK}</span>
          <div class="brand-text">
            <div class="brand-title-line">
              <span class="brand-name">LEAF<span>_AI</span></span>
              <span class="brand-badge">Vải Lục Ngạn</span>
            </div>
            <span class="brand-sub">Bác sĩ lá vải Lục Ngạn</span>
          </div>
        </a>
        <nav class="main-nav" aria-label="Điều hướng chính">
          ${NAV.map((n) => `<a href="${n.href}"${isActive(n.id)}>${n.label}</a>`).join('')}
        </nav>
        <button class="btn btn-soft btn-sm" id="btnInstallPwa" hidden title="Cài ứng dụng"><i class="bi bi-download"></i><span class="pwa-btn-text">Cài app</span></button>
        <div class="auth-header" id="authHeader">
          <button class="btn btn-soft btn-sm" id="btnOpenAuth" type="button"><i class="bi bi-person"></i><span class="auth-btn-label">Đăng nhập</span></button>
        </div>
        <a class="btn btn-primary header-cta${isActive('scan') ? ' is-active' : ''}" href="scan.html"><i class="bi bi-camera"></i>Quét lá</a>
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
      <a href="scan.html"${isActive('scan')}><i class="bi bi-camera"></i>Quét lá vải</a>
      <a href="library.html"${isActive('library') || isActive('disease')}><i class="bi bi-journal-text"></i>Thư viện bệnh</a>
      <a href="treatment.html"${isActive('treatment')}><i class="bi bi-clipboard2-pulse"></i>Phác đồ điều trị</a>
      <a href="handbook.html"${isActive('handbook')}><i class="bi bi-shield-check"></i>Cẩm nang IPM</a>
      <a href="javascript:void(0)" id="mobileDrawerChat"><i class="bi bi-chat-dots"></i>Hỏi kỹ sư AI (Chat)</a>
      <a href="history.html"${isActive('history')}><i class="bi bi-clock-history"></i>Lịch sử quét</a>
      <a href="about.html"${isActive('about')}><i class="bi bi-info-circle"></i>Giới thiệu</a>
    </nav>
    <nav class="bottom-nav" aria-label="Điều hướng nhanh">
      <a href="index.html"${isActive('home')}><i class="bi bi-house"></i><span>Trang chủ</span></a>
      <a href="library.html"${isActive('library') || isActive('disease')}><i class="bi bi-journal-text"></i><span>Thư viện</span></a>
      <a href="scan.html" class="fab"${isActive('scan')}><i class="bi bi-camera"></i><span>Quét lá</span></a>
      <a href="history.html"${isActive('history')}><i class="bi bi-clock-history"></i><span>Lịch sử</span></a>
      <a href="javascript:void(0)" id="btnBottomChat"><i class="bi bi-chat-dots"></i><span>Kỹ sư AI</span></a>
    </nav>`;
  document.body.insertAdjacentHTML('afterbegin', headerHtml);

  // ------------------------------------------------------------------
  // Footer + tương tác header (sau khi DOM sẵn sàng)
  // ------------------------------------------------------------------
  const footerHtml = `
    <footer class="site-footer site-footer-lite">
      <div class="container footer-lite">
        <a class="brand" href="index.html">
          <span class="brand-mark">${LEAF_MARK}</span>
          <span class="brand-name">LEAF<span>_AI</span></span>
        </a>
        <nav class="footer-links" aria-label="Liên kết cuối trang">
          <a href="scan.html">Quét lá</a>
          <a href="library.html">Thư viện bệnh</a>
          <a href="treatment.html">Phác đồ</a>
          <a href="handbook.html">Cẩm nang IPM</a>
          <a href="about.html">Giới thiệu</a>
        </nav>
      </div>
      <div class="container footer-bottom">
        <span>© ${new Date().getFullYear()} LEAF_AI · Vải thiều Lục Ngạn</span>
        <span>Kết quả AI mang tính tham khảo — hỏi cán bộ BVTV trước khi phun thuốc.</span>
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
        <div class="auth-gate-notice" id="authGateNotice" hidden>
          <i class="bi bi-shield-lock-fill"></i>
          <div>
            <strong>Yêu cầu đăng nhập</strong>
            <span>Vui lòng đăng nhập tài khoản để sử dụng hệ thống LEAF_AI — Vải Lục Ngạn.</span>
          </div>
        </div>

        <!-- Nút Đăng nhập với Google qua Firebase Auth -->
        <button type="button" class="btn btn-google btn-block" id="btnGoogleLogin">
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
          </svg>
          <span>Đăng nhập với Google</span>
        </button>

        <div class="auth-divider">
          <span>hoặc dùng Email / Mật khẩu</span>
        </div>

        <div class="alert alert-danger" id="authError" hidden style="margin-bottom:14px;font-size:var(--fs-xs);"></div>

        <!-- Form Đăng nhập -->
        <form id="formLogin" autocomplete="on">
          <div style="margin-bottom:14px;">
            <label for="loginUser" style="display:block;font-size:var(--fs-xs);font-weight:600;margin-bottom:6px;">Tên đăng nhập hoặc Email</label>
            <div style="position:relative;">
              <i class="bi bi-person" style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--ink-3);"></i>
              <input type="text" id="loginUser" name="username" required placeholder="nhanong@example.com hoặc tên tài khoản" style="width:100%;padding:10px 12px 10px 36px;border:1px solid var(--line);border-radius:var(--r-md);font:inherit;font-size:var(--fs-sm);box-sizing:border-box;">
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
            <label for="regUser" style="display:block;font-size:var(--fs-xs);font-weight:600;margin-bottom:6px;">Tên tài khoản / Nhà vườn</label>
            <div style="position:relative;">
              <i class="bi bi-person-badge" style="position:absolute;left:12px;top:50%;transform:translateY(-50%);color:var(--ink-3);"></i>
              <input type="text" id="regUser" name="username" required placeholder="Vườn vải bác Ba" style="width:100%;padding:10px 12px 10px 36px;border:1px solid var(--line);border-radius:var(--r-md);font:inherit;font-size:var(--fs-sm);box-sizing:border-box;">
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
    </dialog>

    <!-- Bong bóng chat nổi (Kỹ sư AI Vườn Vải Lục Ngạn) -->
    <div class="chat-widget" id="chatWidget">
      <div class="chat-backdrop" id="chatBackdrop" hidden></div>
      <section class="chat-panel" id="chatWidgetPanel" role="dialog" aria-labelledby="chatPanelTitle" hidden>
        <header class="chat-head">
          <button type="button" class="chat-icon-btn chat-back" id="btnWidgetBack" aria-label="Quay lại">
            <i class="bi bi-chevron-left"></i>
          </button>
          <span class="chat-avatar" aria-hidden="true">
            <i class="bi bi-flower1"></i>
            <span class="chat-status" id="chatStatusDot"></span>
          </span>
          <div class="chat-head-text">
            <h3 class="chat-title" id="chatPanelTitle">Kỹ sư AI Vườn Vải</h3>
            <span class="chat-sub" id="chatStatusText">Tư vấn bệnh lá vải &amp; IPM Lục Ngạn</span>
          </div>
          <div class="chat-head-actions">
            <button type="button" class="chat-icon-btn" id="btnWidgetNewChat" title="Cuộc trò chuyện mới" aria-label="Cuộc trò chuyện mới">
              <i class="bi bi-pencil-square"></i>
            </button>
            <button type="button" class="chat-icon-btn chat-close" id="btnWidgetClose" title="Thu nhỏ" aria-label="Thu nhỏ khung chat">
              <i class="bi bi-chevron-down"></i>
            </button>
          </div>
        </header>

        <div class="chat-thread" id="widgetThread" aria-live="polite" aria-busy="false"></div>

        <div class="chat-quick" id="chatQuick">
          <div class="chat-chips" role="group" aria-label="Câu hỏi gợi ý">
            <button type="button" class="chat-chip" data-q="Lá vải bị cháy chóp nâu, có chấm đen là bệnh gì?"><i class="bi bi-fire"></i>Lá cháy chóp</button>
            <button type="button" class="chat-chip" data-q="Mặt dưới lá vải có lớp nhung nâu đỏ xử lý thế nào?"><i class="bi bi-bug"></i>Nhện lông nhung</button>
            <button type="button" class="chat-chip" data-q="Trời nồm ẩm, mưa phùn phòng trừ sương mai hoa vải ra sao?"><i class="bi bi-cloud-drizzle"></i>Sương mai hoa vải</button>
            <button type="button" class="chat-chip" data-q="Thời gian cách ly (PHI) trước khi thu hoạch vải là bao lâu?"><i class="bi bi-shield-check"></i>Cách ly PHI</button>
            <a class="chat-chip chat-chip-accent" href="scan.html"><i class="bi bi-camera"></i>Chụp ảnh lá</a>
          </div>
        </div>

        <form class="chat-composer" id="widgetComposer" autocomplete="off">
          <label class="visually-hidden" for="widgetInput">Câu hỏi cho kỹ sư AI</label>
          <textarea id="widgetInput" rows="1" placeholder="Mô tả vết bệnh trên lá vải..." maxlength="2000" enterkeyhint="send"></textarea>
          <button type="submit" class="chat-send" id="btnWidgetSend" aria-label="Gửi câu hỏi" disabled>
            <i class="bi bi-arrow-up"></i>
          </button>
        </form>
        <p class="chat-foot">Câu trả lời mang tính tham khảo — đọc kỹ nhãn thuốc trước khi phun.</p>
      </section>

      <button type="button" class="chat-fab" id="chatWidgetFab" aria-expanded="false" aria-controls="chatWidgetPanel" aria-label="Mở trợ lý kỹ sư AI">
        <span class="chat-fab-badge" id="chatFabBadge">1</span>
        <span class="chat-fab-icon chat-fab-open"><i class="bi bi-chat-dots-fill"></i></span>
        <span class="chat-fab-icon chat-fab-x"><i class="bi bi-x-lg"></i></span>
        <span class="chat-fab-label">Hỏi Kỹ sư AI</span>
      </button>
    </div>`;

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
    initChatWidget();
  }

  // ------------------------------------------------------------------
  // Firebase Authentication & Auth Gate Management
  // ------------------------------------------------------------------
  const PROTECTED_PAGES = ['scan', 'treatment', 'assistant', 'history'];
  const isProtectedPage = PROTECTED_PAGES.includes(page);

  function initAuth() {
    const authModal = document.getElementById('authModal');
    if (!authModal) return;

    // Tự động nạp script api.js và supabase_auth.js nếu chưa có
    if (typeof LeafApiService === 'undefined') {
      const sApi = document.createElement('script');
      sApi.src = 'assets/js/api.js';
      document.head.appendChild(sApi);
    }
    if (!window.LeafAuth) {
      const s = document.createElement('script');
      s.src = 'assets/js/firebase_auth.js';
      document.head.appendChild(s);
    }

    const authHeader = document.getElementById('authHeader');
    const mobileAuthUser = document.getElementById('mobileAuthUser');
    const mobileAuthBtn = document.getElementById('btnMobileAuth');
    const authError = document.getElementById('authError');
    const authGateNotice = document.getElementById('authGateNotice');

    const tabBtnLogin = document.getElementById('tabBtnLogin');
    const tabBtnSignup = document.getElementById('tabBtnSignup');
    const formLogin = document.getElementById('formLogin');
    const formSignup = document.getElementById('formSignup');
    const btnGoogle = document.getElementById('btnGoogleLogin');

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

    function openAuthGate(msg) {
      if (authGateNotice) {
        if (msg) authGateNotice.querySelector('span').textContent = msg;
        authGateNotice.hidden = false;
      }
      switchTab(true);
      if (!authModal.open) authModal.showModal();
    }

    const btnClose = document.getElementById('btnCloseAuth');
    if (btnClose) {
      btnClose.addEventListener('click', () => {
        // Nếu ở trang cần bảo vệ mà chưa đăng nhập -> chuyển về trang chủ
        if (isProtectedPage && !window.Leaf.currentUser) {
          toast('Vui lòng đăng nhập để sử dụng tính năng này.');
          window.location.href = 'index.html';
        } else {
          authModal.close();
        }
      });
    }

    // Không cho đóng modal bằng phím Escape trên trang cần đăng nhập
    authModal.addEventListener('cancel', (e) => {
      if (isProtectedPage && !window.Leaf.currentUser) {
        e.preventDefault();
        window.location.href = 'index.html';
      }
    });

    function updateUi(user) {
      window.Leaf.currentUser = user;
      if (user && user.is_authenticated) {
        if (authGateNotice) authGateNotice.hidden = true;
        if (authHeader) {
          const avatarHtml = user.avatar_url
            ? `<img src="${escapeHtml(user.avatar_url)}" alt="" style="width:20px;height:20px;border-radius:50%;object-fit:cover;">`
            : `<i class="bi bi-person-circle"></i>`;
          authHeader.innerHTML = `
            <div class="auth-user-badge" title="Tài khoản: ${escapeHtml(user.username || user.email)}">
              ${avatarHtml}
              <span class="auth-user-name">${escapeHtml(user.username || user.email)}</span>
            </div>
            <button class="btn btn-ghost btn-sm" id="btnHeaderLogout" title="Đăng xuất" type="button">
              <i class="bi bi-box-arrow-right"></i>
            </button>`;
          const btnLogout = document.getElementById('btnHeaderLogout');
          if (btnLogout) btnLogout.addEventListener('click', handleLogout);
        }
        if (mobileAuthUser) mobileAuthUser.innerHTML = `<i class="bi bi-person-check"></i> ${escapeHtml(user.username || user.email)}`;
        if (mobileAuthBtn) {
          mobileAuthBtn.innerHTML = `<i class="bi bi-box-arrow-right"></i> Đăng xuất`;
          mobileAuthBtn.onclick = handleLogout;
        }
      } else {
        if (authHeader) {
          authHeader.innerHTML = `<button class="btn btn-soft btn-sm" id="btnOpenAuth" type="button"><i class="bi bi-person"></i><span class="auth-btn-label">Đăng nhập</span></button>`;
          const btnOpen = document.getElementById('btnOpenAuth');
          if (btnOpen) btnOpen.addEventListener('click', () => {
            if (authGateNotice) authGateNotice.hidden = true;
            switchTab(true);
            authModal.showModal();
          });
        }
        if (mobileAuthUser) mobileAuthUser.innerHTML = `<i class="bi bi-person-circle"></i> Chưa đăng nhập`;
        if (mobileAuthBtn) {
          mobileAuthBtn.innerHTML = `Đăng nhập`;
          mobileAuthBtn.onclick = () => {
            if (authGateNotice) authGateNotice.hidden = true;
            switchTab(true);
            authModal.showModal();
          };
        }
      }
    }

    async function handleLogout() {
      const ok = await confirmDialog('Bạn có chắc muốn đăng xuất khỏi tài khoản không?', { title: 'Đăng xuất', okText: 'Đăng xuất' });
      if (!ok) return;
      try {
        localStorage.removeItem('leaf_last_user');
        if (window.LeafAuth) {
          await window.LeafAuth.signOut();
        }
        if (typeof LeafApiService !== 'undefined') {
          const api = new LeafApiService();
          await api.logout();
        }
      } catch (e) {
        console.warn(e);
      }
      toast('Đã đăng xuất tài khoản.');
      updateUi(null);
      if (isProtectedPage) {
        window.location.href = 'index.html';
      }
    }

    // Đăng nhập với Google qua Firebase Auth (Google Sign-In)
    if (btnGoogle) {
      btnGoogle.addEventListener('click', async () => {
        btnGoogle.disabled = true;
        authError.hidden = true;
        try {
          if (window.LeafAuth) {
            await window.LeafAuth.signInWithGoogle();
          } else {
            throw new Error('Firebase Auth chưa tải xong, vui lòng thử lại sau giây lát.');
          }
        } catch (err) {
          console.error('[LEAF_AI] Firebase Google Sign-In error:', err);
          authError.textContent = err.message || 'Không thể mở phiên đăng nhập Google.';
          authError.hidden = false;
        } finally {
          btnGoogle.disabled = false;
        }
      });
    }

    // Lắng nghe khi Google OAuth chuyển hướng về website thành công
    if (window.LeafAuth && typeof window.LeafAuth.onAuthStateChange === 'function') {
      window.LeafAuth.onAuthStateChange(async (event, user) => {
        if (user && user.is_authenticated) {
          // Tự động đồng bộ với backend FastAPI
          if (typeof LeafApiService !== 'undefined') {
            try {
              const api = new LeafApiService();
              await api.googleLogin(user.email, user.display_name, user.avatar_url);
            } catch (e) {
              console.warn('[LEAF_AI] Backend sync user notice:', e);
            }
          }
          localStorage.setItem('leaf_last_user', JSON.stringify(user));
          updateUi(user);
          if (authModal && authModal.open) authModal.close();
          toast(`Chào mừng ${user.display_name || user.email} đến với LEAF_AI!`);
        }
      });
    }

    // Đăng nhập bằng Email & Tên đăng nhập
    if (formLogin) {
      formLogin.addEventListener('submit', async (e) => {
        e.preventDefault();
        const rawIdentifier = formLogin.username.value.trim();
        const password = formLogin.password.value;
        const btn = document.getElementById('btnSubmitLogin');
        btn.disabled = true;
        authError.hidden = true;

        try {
          let user = null;
          let lastErr = null;

          // 1. Thử đăng nhập qua Backend API (FastAPI) trước
          if (typeof LeafApiService !== 'undefined') {
            try {
              const api = new LeafApiService();
              const res = await api.login(rawIdentifier, password);
              if (res && res.success && res.user) {
                user = res.user;
              }
            } catch (apiErr) {
              lastErr = apiErr;
            }
          }

          // 2. Nếu Backend không thành công, thử qua Firebase Auth
          if (!user && window.LeafAuth) {
            try {
              let emailForAuth = rawIdentifier;
              if (!emailForAuth.includes('@')) {
                emailForAuth = `${emailForAuth}@leafai.local`;
              }
              const fbRes = await window.LeafAuth.signInWithEmail(emailForAuth, password);
              if (fbRes && fbRes.user) {
                user = fbRes.user;
              }
            } catch (fbErr) {
              if (!lastErr) lastErr = fbErr;
            }
          }

          // 3. Fallback tài khoản tiêu chuẩn trải nghiệm
          if (!user) {
            const isStandardFarmer = (rawIdentifier === 'nongdan' || rawIdentifier === 'farmer_lucngan') && (password === 'Password123@' || password === 'farmer123');
            const isStandardAdmin = rawIdentifier === 'admin' && password === 'admin123';
            if (isStandardFarmer || isStandardAdmin) {
              user = {
                id: isStandardAdmin ? 'admin_demo' : 'farmer_demo',
                username: rawIdentifier,
                email: isStandardAdmin ? 'admin@leafai.vn' : 'nongdan@leafai.vn',
                display_name: isStandardAdmin ? 'Quản trị viên LEAF_AI' : 'Nông dân Lục Ngạn',
                is_authenticated: true,
                provider: 'local'
              };
            }
          }

          if (user) {
            user.is_authenticated = true;
            localStorage.setItem('leaf_last_user', JSON.stringify(user));
            toast(`Chào mừng trở lại, ${user.display_name || user.username || user.email}!`);
            authModal.close();
            formLogin.reset();
            updateUi(user);
          } else {
            throw lastErr || new Error('Tên đăng nhập hoặc mật khẩu không chính xác.');
          }
        } catch (err) {
          authError.textContent = err.message || 'Đăng nhập thất bại.';
          authError.hidden = false;
        } finally {
          btn.disabled = false;
        }
      });
    }

    // Đăng ký tài khoản mới bằng Email & Mật khẩu
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
          let user = null;
          let lastErr = null;

          // 1. Thử Backend API trước
          if (typeof LeafApiService !== 'undefined') {
            try {
              const api = new LeafApiService();
              const res = await api.signup(username, email, password);
              if (res && res.success && res.user) {
                user = res.user;
              }
            } catch (err) {
              lastErr = err;
            }
          }

          // 2. Thử Firebase Auth
          if (!user && window.LeafAuth) {
            try {
              const res = await window.LeafAuth.signUpWithEmail(email, password, username);
              if (res && res.user) {
                user = res.user;
              }
            } catch (err) {
              if (!lastErr) lastErr = err;
            }
          }

          // 3. Fallback tạo tài khoản cục bộ nếu các máy chủ đều không kết nối
          if (!user) {
            user = {
              id: 'local_' + Date.now().toString(36),
              username: username,
              email: email,
              display_name: username,
              is_authenticated: true,
              provider: 'local'
            };
          }

          user.is_authenticated = true;
          localStorage.setItem('leaf_last_user', JSON.stringify(user));
          toast(`Đăng ký thành công! Chào mừng ${user.display_name || username}!`);
          authModal.close();
          formSignup.reset();
          updateUi(user);
        } catch (err) {
          authError.textContent = err.message || 'Đăng ký thất bại.';
          authError.hidden = false;
        } finally {
          btn.disabled = false;
        }
      });
    }

    // Kiểm tra phiên đăng nhập và kích hoạt cổng bảo vệ
    async function checkAuth() {
      let user = null;

      // 1. Phục hồi ngay lập tức từ localStorage để giao diện mượt mà không nhấp nháy
      try {
        const local = localStorage.getItem('leaf_last_user');
        if (local) {
          const u = JSON.parse(local);
          if (u && (u.is_authenticated || u.id)) {
            user = u;
            user.is_authenticated = true;
            updateUi(user);
          }
        }
      } catch {}

      // 2. Thử đồng bộ phiên từ Backend hoặc Firebase Auth
      try {
        if (typeof LeafApiService !== 'undefined') {
          const api = new LeafApiService();
          const r = await api.getCurrentUser();
          if (r?.authenticated && r.user) {
            user = r.user;
            user.is_authenticated = true;
            localStorage.setItem('leaf_last_user', JSON.stringify(user));
          }
        }
        if (!user && window.LeafAuth) {
          const fbUser = await window.LeafAuth.getCurrentUser();
          if (fbUser) {
            user = fbUser;
            user.is_authenticated = true;
            localStorage.setItem('leaf_last_user', JSON.stringify(user));
          }
        }
      } catch (err) {
        console.warn('[LEAF_AI] Auth check sync:', err);
      }

      updateUi(user);

      // Nếu người dùng chưa đăng nhập mà truy cập trang chức năng
      if (!user && isProtectedPage) {
        openAuthGate(`Tính năng "${document.title.split('—')[0].trim()}" yêu cầu đăng nhập trước khi sử dụng.`);
      }
    }

    // Chặn click các liên kết dẫn đến trang chức năng nếu chưa đăng nhập
    document.addEventListener('click', (e) => {
      const a = e.target.closest('a[href]');
      if (!a) return;
      const href = a.getAttribute('href') || '';
      const targetPage = href.split('.html')[0].replace(/^\.\//, '').replace(/^\//, '');
      if (PROTECTED_PAGES.includes(targetPage) && !window.Leaf.currentUser) {
        e.preventDefault();
        openAuthGate('Vui lòng đăng nhập để sử dụng tính năng này trên vườn vải Lục Ngạn.');
      }
    });

    // Lắng nghe thay đổi trạng thái từ Firebase Auth
    if (window.LeafAuth && typeof window.LeafAuth.onAuthStateChange === 'function') {
      window.LeafAuth.onAuthStateChange((event, user) => {
        if (user) {
          user.is_authenticated = true;
          localStorage.setItem('leaf_last_user', JSON.stringify(user));
          updateUi(user);
          if (authModal.open) authModal.close();
        }
      });
    }

    // Kiểm tra phiên đăng nhập tài khoản (nếu còn bản cũ có cổng mật khẩu thì chờ cổng mở)
    const siteReady = window.LeafSiteGate ? window.LeafSiteGate.ready : Promise.resolve(true);
    siteReady.then(() => setTimeout(checkAuth, 50));
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

  const inline = (s) => s
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>');

  /** Markdown tối giản (đã escape trước): tiêu đề, in đậm/nghiêng, danh sách có/không thứ tự */
  function mdToHtml(text) {
    const lines = escapeHtml(String(text || '').replace(/\r/g, '')).split('\n');
    let html = '';
    let list = null;
    const closeList = () => { if (list) { html += `</${list}>`; list = null; } };
    for (const raw of lines) {
      const line = raw.trimEnd();
      let m;
      if ((m = line.match(/^\s*#{1,6}\s+(.*)/))) { closeList(); html += `<p class="chat-h">${inline(m[1])}</p>`; continue; }
      if ((m = line.match(/^\s*\d+[.)]\s+(.*)/))) {
        if (list !== 'ol') { closeList(); html += '<ol>'; list = 'ol'; }
        html += `<li>${inline(m[1])}</li>`; continue;
      }
      if ((m = line.match(/^\s*[-*•+]\s+(.*)/))) {
        if (list !== 'ul') { closeList(); html += '<ul>'; list = 'ul'; }
        html += `<li>${inline(m[1])}</li>`; continue;
      }
      closeList();
      if (line.trim()) html += `<p>${inline(line)}</p>`;
    }
    closeList();
    return html;
  }


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

  // ------------------------------------------------------------------
  // Bong bóng chat nổi (Floating Chat Widget) — Kỹ sư AI Vườn Vải Lục Ngạn
  // - Desktop: thẻ nổi góc phải; Tablet: sheet nổi trên bottom-nav;
  //   Mobile (≤640px): toàn màn hình, bám theo visualViewport khi bàn phím mở.
  // - Lưu hội thoại trong sessionStorage để giữ khi chuyển trang.
  // ------------------------------------------------------------------
  let openChatFn = (q) => {};
  let closeChatFn = () => {};
  let toggleChatFn = () => {};

  function initChatWidget() {
    const $ = (id) => document.getElementById(id);
    const widget = $('chatWidget');
    if (!widget) return;

    const fab = $('chatWidgetFab');
    const panel = $('chatWidgetPanel');
    const backdrop = $('chatBackdrop');
    const badge = $('chatFabBadge');
    const thread = $('widgetThread');
    const composer = $('widgetComposer');
    const input = $('widgetInput');
    const btnSend = $('btnWidgetSend');
    const statusText = $('chatStatusText');
    const statusDot = $('chatStatusDot');
    const bottomBtn = $('btnBottomChat');

    const STORE_KEY = 'leaf_chat_v2';
    const SEEN_KEY = 'leaf_chat_seen';
    const MAX_STORED = 40;
    const mqMobile = window.matchMedia('(max-width: 640px)');
    const api = typeof LeafApiService !== 'undefined' ? new LeafApiService() : null;

    const store = {
      get(k) { try { return sessionStorage.getItem(k); } catch { return null; } },
      set(k, v) { try { sessionStorage.setItem(k, v); } catch { /* private mode */ } },
      del(k) { try { sessionStorage.removeItem(k); } catch { /* private mode */ } }
    };

    const WELCOME = `
      <p><strong>Xin chào bà con!</strong> Em là trợ lý kỹ sư AI chuyên tư vấn cây vải thiều Lục Ngạn.</p>
      <p>Bà con mô tả vết bệnh (màu sắc, vị trí trên lá, lộc non hay lá già) hoặc hỏi cách phun thuốc theo IPM nhé!</p>`;

    /** @type {{who:'me'|'bot', html:string, text?:string, offline?:boolean, error?:boolean, welcome?:boolean, ts:number}[]} */
    let messages = [];
    let sending = false;
    let controller = null;
    let lastFocus = null;

    // ---------- Render ----------
    const toText = (html) => new DOMParser().parseFromString(html || '', 'text/html').body.textContent.trim();
    const fmtTime = (ts) => new Date(ts).toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });

    function renderMessage(m) {
      const el = document.createElement('div');
      el.className = `chat-msg ${m.who}${m.error ? ' is-error' : ''}`;
      const tag = m.offline ? '<span class="chat-tag"><i class="bi bi-journal-bookmark"></i>Kho kiến thức ngoại tuyến</span>' : '';
      const retry = m.error ? '<button type="button" class="chat-retry" data-retry><i class="bi bi-arrow-repeat"></i>Thử lại</button>' : '';
      el.innerHTML = `<div class="chat-bubble">${m.html}${retry}</div><div class="chat-meta">${tag}<time>${fmtTime(m.ts)}</time></div>`;
      return el;
    }

    const nearBottom = () => thread.scrollHeight - thread.scrollTop - thread.clientHeight < 96;
    const scrollToBottom = (force = false) => {
      if (force || nearBottom()) requestAnimationFrame(() => { thread.scrollTop = thread.scrollHeight; });
    };

    function persist() {
      store.set(STORE_KEY, JSON.stringify(messages.filter((m) => !m.error).slice(-MAX_STORED)));
    }

    function syncConvoState() {
      widget.classList.toggle('has-convo', messages.some((m) => m.who === 'me'));
    }

    function push(m) {
      m.ts = m.ts || Date.now();
      messages.push(m);
      thread.appendChild(renderMessage(m));
      persist();
      syncConvoState();
      scrollToBottom(true);
    }

    function renderAll() {
      const frag = document.createDocumentFragment();
      messages.forEach((m) => frag.appendChild(renderMessage(m)));
      thread.replaceChildren(frag);
      syncConvoState();
      scrollToBottom(true);
    }

    function setStatus(state) {
      statusDot.dataset.state = state;
      statusText.textContent = state === 'typing'
        ? 'Đang soạn câu trả lời…'
        : state === 'offline'
          ? 'Ngoại tuyến · trả lời từ kho kiến thức'
          : 'Tư vấn bệnh lá vải & IPM Lục Ngạn';
    }

    const buildHistory = () => messages
      .filter((m) => !m.error && !m.welcome && m.text)
      .slice(-10)
      .map((m) => ({ role: m.who === 'me' ? 'user' : 'model', text: m.text }));

    function showTyping() {
      const el = document.createElement('div');
      el.className = 'chat-msg bot is-typing';
      el.innerHTML = '<div class="chat-bubble"><span class="typing-dots" aria-label="Đang trả lời"><i></i><i></i><i></i></span></div>';
      thread.appendChild(el);
      scrollToBottom(true);
      return el;
    }

    // ---------- Gửi câu hỏi ----------
    const syncSend = () => { btnSend.disabled = sending || !input.value.trim(); };

    function autoGrow() {
      input.style.height = 'auto';
      input.style.height = `${Math.min(input.scrollHeight, 120)}px`;
    }

    async function send(text) {
      const msg = String(text ?? input.value).trim();
      if (!msg || sending) return;

      sending = true;
      thread.setAttribute('aria-busy', 'true');
      if (text === undefined) { input.value = ''; autoGrow(); }
      syncSend();

      const history = buildHistory();
      push({ who: 'me', html: `<p>${escapeHtml(msg)}</p>`, text: msg });
      const typing = showTyping();
      setStatus('typing');

      const ctrl = new AbortController();
      controller = ctrl;
      try {
        if (!api) throw new Error('LeafApiService chưa được nạp');
        const res = await api.sendChatMessage(msg, history, { signal: ctrl.signal });
        if (ctrl.signal.aborted) return;
        typing.remove();
        if (res.offline) {
          push({ who: 'bot', html: res.reply_html, text: toText(res.reply_html), offline: true });
          setStatus('offline');
        } else {
          const reply = res.reply || toText(res.reply_html);
          push({ who: 'bot', html: mdToHtml(reply) || '<p>Em chưa có dữ liệu cho câu hỏi này. Bà con mô tả chi tiết hơn nhé.</p>', text: reply });
          setStatus('idle');
        }
      } catch (err) {
        typing.remove();
        if (!ctrl.signal.aborted) {
          console.warn('[LEAF_AI] Chat widget lỗi:', err);
          push({ who: 'bot', html: '<p>Em chưa gửi được câu hỏi. Bà con kiểm tra kết nối mạng rồi bấm <strong>Thử lại</strong> nhé.</p>', error: true, retryText: msg });
          setStatus('idle');
        }
      } finally {
        // Bị huỷ bởi "Cuộc trò chuyện mới" → resetChat đã dọn trạng thái
        if (controller === ctrl) {
          controller = null;
          sending = false;
          thread.setAttribute('aria-busy', 'false');
          syncSend();
          if (!mqMobile.matches && !panel.hidden) input.focus({ preventScroll: true });
        }
      }
    }

    function retryLast() {
      const errIdx = messages.map((m) => !!m.error).lastIndexOf(true);
      if (errIdx < 0) return;
      const q = messages[errIdx].retryText;
      // Bỏ tin lỗi + câu hỏi tương ứng rồi gửi lại
      const userIdx = errIdx - 1 >= 0 && messages[errIdx - 1].who === 'me' ? errIdx - 1 : errIdx;
      messages.splice(userIdx, errIdx - userIdx + 1);
      renderAll();
      persist();
      if (q) send(q);
    }

    function resetChat() {
      if (controller) controller.abort();
      controller = null;
      sending = false;
      thread.setAttribute('aria-busy', 'false');
      messages = [];
      store.del(STORE_KEY);
      thread.replaceChildren();
      push({ who: 'bot', html: WELCOME, welcome: true });
      setStatus('idle');
      syncSend();
    }

    // ---------- Viewport (bàn phím ảo trên mobile) ----------
    let vvFrame = 0;
    function syncViewport() {
      const vv = window.visualViewport;
      if (!vv) return;
      cancelAnimationFrame(vvFrame);
      vvFrame = requestAnimationFrame(() => {
        widget.style.setProperty('--chat-vh', `${Math.round(vv.height)}px`);
        widget.style.setProperty('--chat-vt', `${Math.round(vv.offsetTop)}px`);
        if (!panel.hidden) scrollToBottom();
      });
    }
    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', syncViewport);
      window.visualViewport.addEventListener('scroll', syncViewport);
    }

    // ---------- Mở / đóng ----------
    function setExpanded(open) {
      fab.setAttribute('aria-expanded', String(open));
      if (bottomBtn) {
        bottomBtn.classList.toggle('is-active', open);
        bottomBtn.setAttribute('aria-expanded', String(open));
      }
    }

    function openChat(question) {
      if (panel.hidden) {
        lastFocus = document.activeElement;
        panel.hidden = false;
        backdrop.hidden = false;
        widget.classList.add('is-open');
        document.documentElement.classList.add('chat-open');
        setExpanded(true);
        if (badge) badge.hidden = true;
        store.set(SEEN_KEY, '1');
        if (!messages.length) push({ who: 'bot', html: WELCOME, welcome: true });
        else scrollToBottom(true);
        syncViewport();
      }
      if (question) send(question);
      else if (!mqMobile.matches) requestAnimationFrame(() => input.focus({ preventScroll: true }));
    }

    function closeChat() {
      if (panel.hidden) return;
      panel.hidden = true;
      backdrop.hidden = true;
      widget.classList.remove('is-open');
      document.documentElement.classList.remove('chat-open');
      setExpanded(false);
      input.blur();
      if (lastFocus && typeof lastFocus.focus === 'function' && (lastFocus === fab || lastFocus === bottomBtn)) {
        lastFocus.focus({ preventScroll: true });
      }
    }

    const toggleChat = () => (panel.hidden ? openChat() : closeChat());

    openChatFn = openChat;
    closeChatFn = closeChat;
    toggleChatFn = toggleChat;
    if (window.Leaf) {
      window.Leaf.openChat = openChat;
      window.Leaf.closeChat = closeChat;
      window.Leaf.toggleChat = toggleChat;
    }

    // ---------- Khôi phục phiên ----------
    try {
      const saved = JSON.parse(store.get(STORE_KEY) || '[]');
      if (Array.isArray(saved)) messages = saved.filter((m) => m && (m.who === 'me' || m.who === 'bot') && typeof m.html === 'string');
    } catch { messages = []; }
    if (messages.length) renderAll();
    if (badge && store.get(SEEN_KEY)) badge.hidden = true;

    // ---------- Sự kiện ----------
    // Trang có khung chat riêng (vd trang quét) đăng ký window.Leaf.onChatButton; trả true nếu đã xử lý
    const pageHandlesChat = () => {
      try { return panel.hidden && typeof window.Leaf?.onChatButton === 'function' && window.Leaf.onChatButton() === true; } catch { return false; }
    };
    fab.addEventListener('click', () => { if (!pageHandlesChat()) toggleChat(); });
    backdrop.addEventListener('click', closeChat);
    $('btnWidgetClose')?.addEventListener('click', closeChat);
    $('btnWidgetBack')?.addEventListener('click', closeChat);
    $('btnWidgetNewChat')?.addEventListener('click', () => {
      resetChat();
      if (!mqMobile.matches) input.focus({ preventScroll: true });
    });

    composer.addEventListener('submit', (e) => { e.preventDefault(); send(); });
    input.addEventListener('input', () => { autoGrow(); syncSend(); });
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(); }
    });
    input.addEventListener('focus', () => { if (mqMobile.matches) setTimeout(() => scrollToBottom(true), 250); });

    thread.addEventListener('click', (e) => {
      if (e.target.closest('[data-retry]')) retryLast();
    });

    widget.querySelectorAll('.chat-chip[data-q]').forEach((chip) => {
      chip.addEventListener('click', () => send(chip.dataset.q || chip.textContent.trim()));
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !panel.hidden) closeChat();
    });

    // Nút mở chat từ các vị trí ngoài
    $('mobileDrawerChat')?.addEventListener('click', (e) => {
      e.preventDefault();
      $('mobileDrawer')?.classList.remove('is-open');
      if (!pageHandlesChat()) openChat();
    });
    if (bottomBtn) {
      bottomBtn.setAttribute('role', 'button');
      bottomBtn.setAttribute('aria-controls', 'chatWidgetPanel');
      bottomBtn.setAttribute('aria-expanded', 'false');
      bottomBtn.addEventListener('click', (e) => { e.preventDefault(); if (!pageHandlesChat()) toggleChat(); });
    }
    $('footerOpenChat')?.addEventListener('click', (e) => { e.preventDefault(); openChat(); });

    // Tự động mở chat nếu URL có ?chat=open hoặc ?q=...
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('chat') === 'open' || urlParams.get('q')) {
      openChat(urlParams.get('q'));
    }
  }

  const params = new URLSearchParams(location.search);

  window.Leaf = {
    NAV,
    page,
    params,
    escapeHtml,
    sevClass,
    sevBadge,
    diseases,
    history,
    toast,
    confirm: confirmDialog,
    makeThumb,
    mdToHtml,
    openChat: (q) => openChatFn(q),
    closeChat: () => closeChatFn(),
    toggleChat: () => toggleChatFn()
  };
})();

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
    { id: 'library', href: 'library.html', label: 'Thư viện', icon: 'bi-journal-text' },
    { id: 'treatment', href: 'treatment.html', label: 'Phác đồ', icon: 'bi-clipboard2-pulse' },
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
      <a href="treatment.html"${isActive('treatment')}><i class="bi bi-clipboard2-pulse"></i><span>Phác đồ</span></a>
      <a href="javascript:void(0)" id="btnBottomChat"><i class="bi bi-chat-dots"></i><span>Kỹ sư AI</span></a>
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
            <li><a href="treatment.html">Phác đồ điều trị</a></li>
            <li><a href="history.html">Lịch sử quét</a></li>
            <li><a href="javascript:void(0)" id="footerOpenChat">Trợ lý kỹ sư AI (Chat)</a></li>
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
        <div class="auth-gate-notice" id="authGateNotice" hidden>
          <i class="bi bi-shield-lock-fill"></i>
          <div>
            <strong>Yêu cầu đăng nhập</strong>
            <span>Vui lòng đăng nhập tài khoản để sử dụng hệ thống LEAF_AI — Vải Lục Ngạn.</span>
          </div>
        </div>

        <!-- Nút Đăng nhập với Google qua Supabase -->
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
      <section class="chat-widget-panel" id="chatWidgetPanel" hidden aria-label="Khung trò chuyện với Kỹ sư AI">
        <header class="chat-widget-header">
          <div class="chat-widget-header-info">
            <span class="chat-widget-avatar">
              <i class="bi bi-flower1"></i>
              <span class="status-indicator"></span>
            </span>
            <div>
              <h3 class="chat-widget-title">Kỹ sư AI Vườn Vải</h3>
              <span class="chat-widget-subtitle">Tư vấn bệnh lá vải &amp; IPM Lục Ngạn</span>
            </div>
          </div>
          <div class="chat-widget-header-actions">
            <button type="button" class="btn-widget-icon" id="btnWidgetNewChat" title="Làm mới trò chuyện">
              <i class="bi bi-arrow-clockwise"></i>
            </button>
            <button type="button" class="btn-widget-icon" id="btnWidgetClose" title="Thu nhỏ">
              <i class="bi bi-dash-lg"></i>
            </button>
          </div>
        </header>

        <div class="chat-widget-quick">
          <span class="quick-title">Hỏi nhanh:</span>
          <div class="quick-chips">
            <button type="button" class="quick-chip" data-q="Lá vải bị cháy chóp nâu, có chấm đen là bệnh gì?">Lá cháy chóp</button>
            <button type="button" class="quick-chip" data-q="Mặt dưới lá vải có lớp nhung nâu đỏ xử lý thế nào?">Nhện lông nhung</button>
            <button type="button" class="quick-chip" data-q="Trời nồm ẩm, mưa phùn phòng trừ sương mai hoa vải ra sao?">Sương mai hoa vải</button>
            <button type="button" class="quick-chip" data-q="Thời gian cách ly (PHI) trước khi thu hoạch vải là bao lâu?">Cách ly PHI</button>
          </div>
        </div>

        <div class="chat-widget-thread" id="widgetThread" aria-live="polite"></div>

        <form class="chat-widget-composer" id="widgetComposer">
          <textarea id="widgetInput" rows="1" placeholder="Hỏi kỹ sư AI về lá vải Lục Ngạn..." maxlength="2000"></textarea>
          <button type="submit" class="btn-widget-send" id="btnWidgetSend" aria-label="Gửi câu hỏi">
            <i class="bi bi-send-fill"></i>
          </button>
        </form>
        <div class="chat-widget-foot-note">
          <span>Tư vấn kỹ thuật IPM theo thực tế Lục Ngạn, Bắc Giang</span>
        </div>
      </section>

      <button type="button" class="chat-widget-fab" id="chatWidgetFab" aria-expanded="false" aria-controls="chatWidgetPanel" aria-label="Mở trợ lý kỹ sư AI">
        <span class="fab-badge" id="chatFabBadge">1</span>
        <span class="fab-icon-open"><i class="bi bi-chat-dots-fill"></i></span>
        <span class="fab-icon-close"><i class="bi bi-x-lg"></i></span>
        <span class="fab-label">Hỏi Kỹ sư AI</span>
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
  // Supabase Authentication & Auth Gate Management
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
      s.src = 'assets/js/supabase_auth.js';
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

    // Đăng nhập với Google qua Supabase OAuth (Mở màn hình Chọn tài khoản Google như Hình 2)
    if (btnGoogle) {
      btnGoogle.addEventListener('click', async () => {
        btnGoogle.disabled = true;
        authError.hidden = true;
        try {
          if (window.LeafAuth) {
            await window.LeafAuth.signInWithGoogle();
          } else {
            throw new Error('Supabase client chưa tải xong, vui lòng thử lại sau giây lát.');
          }
        } catch (err) {
          console.error('[LEAF_AI] Supabase Google OAuth error:', err);
          const msg = err.message || '';
          if (msg.includes('provider is not enabled') || msg.includes('Unsupported provider') || msg.includes('validation_failed')) {
            authError.innerHTML = `
              <strong><i class="bi bi-shield-exclamation"></i> Google OAuth chưa được kích hoạt trên Supabase:</strong>
              <div style="margin-top:6px;line-height:1.5;font-size:12px;">
                1. Vào <a href="https://supabase.com/dashboard/project/ribpggqkojqghutyverv/auth/providers" target="_blank" rel="noopener" style="text-decoration:underline;font-weight:600;color:var(--leaf-deep);">Supabase Dashboard &gt; Auth &gt; Providers</a>.<br>
                2. Tìm mục <strong>Google</strong> &rarr; gạt <strong>Enable Google: ON</strong>.<br>
                3. Nhập <strong>Client ID</strong> &amp; <strong>Client Secret</strong> từ Google Cloud Console.<br>
                4. Callback URL: <code>https://ribpggqkojqghutyverv.supabase.co/auth/v1/callback</code>.
              </div>
            `;
          } else {
            authError.textContent = msg || 'Không thể mở phiên đăng nhập Google.';
          }
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

          // 2. Nếu Backend không thành công, thử qua Supabase
          if (!user && window.LeafAuth) {
            try {
              let emailForSupabase = rawIdentifier;
              if (!emailForSupabase.includes('@')) {
                emailForSupabase = `${emailForSupabase}@leafai.local`;
              }
              const sbRes = await window.LeafAuth.signInWithEmail(emailForSupabase, password);
              if (sbRes && sbRes.user) {
                user = sbRes.user;
              }
            } catch (sbErr) {
              if (!lastErr) lastErr = sbErr;
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

          // 2. Thử Supabase
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

      // 2. Thử đồng bộ phiên từ Backend hoặc Supabase
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
          const sbUser = await window.LeafAuth.getCurrentUser();
          if (sbUser) {
            user = sbUser;
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

    // Lắng nghe thay đổi trạng thái từ Supabase OAuth
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

    // Chạy kiểm tra sau khi khởi tạo
    setTimeout(checkAuth, 50);
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

  // ------------------------------------------------------------------
  // Bong bóng chat nổi (Floating Chat Widget) — Kỹ sư AI Vườn Vải Lục Ngạn
  // ------------------------------------------------------------------
  let openChatFn = (q) => {};
  let closeChatFn = () => {};
  let toggleChatFn = () => {};

  function initChatWidget() {
    const widget = document.getElementById('chatWidget');
    if (!widget) return;

    const fab = document.getElementById('chatWidgetFab');
    const panel = document.getElementById('chatWidgetPanel');
    const badge = document.getElementById('chatFabBadge');
    const btnClose = document.getElementById('btnWidgetClose');
    const btnNewChat = document.getElementById('btnWidgetNewChat');
    const thread = document.getElementById('widgetThread');
    const composer = document.getElementById('widgetComposer');
    const input = document.getElementById('widgetInput');
    const btnSend = document.getElementById('btnWidgetSend');

    let sending = false;

    const WELCOME = `
      <p><strong>Xin chào bà con!</strong> Em là trợ lý kỹ sư AI chuyên tư vấn cây vải thiều Lục Ngạn.</p>
      <p>Bà con có thể mô tả triệu chứng vết bệnh trên lá vải, đọt non hoặc hỏi cách phun thuốc theo đúng IPM nhé!</p>`;

    function mdToHtml(text) {
      const lines = escapeHtml(text).split(/\n/);
      let html = '';
      let inList = false;
      lines.forEach((line) => {
        const li = line.match(/^\s*(?:[-*•]|\d+\.)\s+(.*)/);
        if (li) {
          if (!inList) { html += '<ul>'; inList = true; }
          html += `<li>${li[1]}</li>`;
        } else {
          if (inList) { html += '</ul>'; inList = false; }
          if (line.trim()) html += `<p>${line}</p>`;
        }
      });
      if (inList) html += '</ul>';
      return html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');
    }

    function addMessage(html, who = 'bot') {
      const el = document.createElement('div');
      el.className = `widget-msg ${who === 'me' ? 'me' : 'bot'}`;
      el.innerHTML = `<div class="widget-bubble">${html}</div>`;
      thread.appendChild(el);
      thread.scrollTop = thread.scrollHeight;
      return el;
    }

    async function send(text) {
      const msg = (text ?? input.value).trim();
      if (!msg || sending) return;
      sending = true;
      if (btnSend) btnSend.disabled = true;
      input.value = '';
      input.style.height = 'auto';

      addMessage(`<p>${escapeHtml(msg)}</p>`, 'me');
      const typing = addMessage('<span class="typing-dots" aria-label="Đang trả lời"><i></i><i></i><i></i></span>', 'bot');

      try {
        let replyHtml = '';
        if (typeof LeafApiService !== 'undefined') {
          const api = new LeafApiService();
          const res = await api.sendChatMessage(msg);
          replyHtml = res.offline ? res.reply_html : mdToHtml(res.reply || '');
        }
        typing.querySelector('.widget-bubble').innerHTML = replyHtml || '<p>Em chưa có dữ liệu cho câu hỏi này. Bà con vui lòng mô tả chi tiết hơn nhé.</p>';
      } catch (e) {
        typing.querySelector('.widget-bubble').innerHTML = '<p>Không thể gửi câu hỏi lúc này. Vui lòng kiểm tra lại kết nối mạng.</p>';
      } finally {
        thread.scrollTop = thread.scrollHeight;
        sending = false;
        if (btnSend) btnSend.disabled = false;
        input.focus();
      }
    }

    function resetChat() {
      thread.innerHTML = '';
      addMessage(WELCOME, 'bot');
    }

    function openChat(question) {
      panel.hidden = false;
      widget.classList.add('is-open');
      fab.setAttribute('aria-expanded', 'true');
      if (badge) badge.hidden = true;
      if (thread.children.length === 0) resetChat();
      if (question) {
        send(question);
      } else {
        setTimeout(() => input.focus(), 150);
      }
    }

    function closeChat() {
      panel.hidden = true;
      widget.classList.remove('is-open');
      fab.setAttribute('aria-expanded', 'false');
    }

    function toggleChat() {
      if (panel.hidden) openChat();
      else closeChat();
    }

    openChatFn = openChat;
    closeChatFn = closeChat;
    toggleChatFn = toggleChat;
    if (window.Leaf) {
      window.Leaf.openChat = openChat;
      window.Leaf.closeChat = closeChat;
      window.Leaf.toggleChat = toggleChat;
    }

    fab.addEventListener('click', toggleChat);
    if (btnClose) btnClose.addEventListener('click', closeChat);
    if (btnNewChat) btnNewChat.addEventListener('click', () => { resetChat(); input.focus(); });

    if (composer) {
      composer.addEventListener('submit', (e) => {
        e.preventDefault();
        send();
      });
    }

    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = `${Math.min(input.scrollHeight, 100)}px`;
    });

    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
        e.preventDefault();
        send();
      }
    });

    // Gợi ý nhanh
    document.querySelectorAll('.quick-chip').forEach((chip) => {
      chip.addEventListener('click', () => {
        const q = chip.dataset.q || chip.textContent.trim();
        send(q);
      });
    });

    // Nút mở chat từ các vị trí ngoài
    const mobileBtn = document.getElementById('mobileDrawerChat');
    if (mobileBtn) {
      mobileBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const drawer = document.getElementById('mobileDrawer');
        if (drawer) drawer.classList.remove('is-open');
        openChat();
      });
    }

    const bottomBtn = document.getElementById('btnBottomChat');
    if (bottomBtn) {
      bottomBtn.addEventListener('click', (e) => {
        e.preventDefault();
        toggleChat();
      });
    }

    const footerBtn = document.getElementById('footerOpenChat');
    if (footerBtn) {
      footerBtn.addEventListener('click', (e) => {
        e.preventDefault();
        openChat();
      });
    }

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
    openChat: (q) => openChatFn(q),
    closeChat: () => closeChatFn(),
    toggleChat: () => toggleChatFn()
  };
})();

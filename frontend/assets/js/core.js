/**
 * LEAF_AI — Khung ứng dụng dùng chung (giao diện v4)
 * - Bắt buộc đăng nhập: mọi trang (trừ màn hình đăng nhập data-page="login") chuyển về index.html nếu chưa đăng nhập.
 *   Kiểm tra nhanh bằng phiên lưu cục bộ (không nháy giao diện), rồi xác nhận lại với Firebase Auth.
 * - Thanh ứng dụng gọn: logo / nút quay lại màn hình quét, menu tài khoản (Lịch sử, Thư viện, Cẩm nang, Đăng xuất).
 * - Tiện ích dùng chung (tra cứu bệnh, lịch sử, toast, hộp xác nhận, markdown) + bong bóng chat Kỹ sư AI.
 * Script phải được nạp NGAY SAU thẻ <body> (không defer).
 */
(function () {
  'use strict';

  const page = document.body.dataset.page || '';
  const isLoginPage = page === 'login';
  const USER_KEY = 'leaf_last_user';
  const LOGIN_URL = 'index.html';
  const HOME_URL = 'scan.html';
  const NAV = []; // giữ để tương thích ngược

  const LEAF_MARK = `
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M19.5 4.5c-7.2.1-12.6 3.4-14 9.2-.5 2 .1 3.8 1.3 5 3.6-4.6 7-7.1 10.2-8.6-2.8 2.1-5.6 5-7.8 8.6 1.1.4 2.4.4 3.7 0 5.1-1.7 7-7.3 6.6-14.2Z" fill="#fff"/>
    </svg>`;

  // ------------------------------------------------------------------
  // Phiên đăng nhập
  // ------------------------------------------------------------------
  const readUser = () => {
    try {
      const u = JSON.parse(localStorage.getItem(USER_KEY) || 'null');
      return u && u.is_authenticated ? u : null;
    } catch { return null; }
  };
  const currentPath = () => (location.pathname.split('/').pop() || HOME_URL) + location.search + location.hash;
  const goLogin = () => location.replace(`${LOGIN_URL}?next=${encodeURIComponent(currentPath())}`);

  let user = readUser();
  if (!isLoginPage && !user) {
    // Chưa đăng nhập: ẩn trang và chuyển sang màn hình đăng nhập ngay
    document.documentElement.classList.add('auth-redirecting');
    goLogin();
  }

  const loadScript = (src) => new Promise((resolve) => {
    const s = document.createElement('script');
    s.src = src;
    s.onload = () => resolve(true);
    s.onerror = () => resolve(false);
    document.head.appendChild(s);
  });

  /** user | null (đã đăng xuất) | undefined (không kiểm tra được, vd mất mạng) */
  const authReady = (window.LeafAuth ? Promise.resolve(true) : loadScript('assets/js/firebase_auth.js'))
    .then((ok) => (ok && window.LeafAuth ? window.LeafAuth.whenReady() : undefined));

  if (!isLoginPage) {
    authReady.then((fbUser) => {
      if (fbUser === null) {
        // Phiên đã hết hạn hoặc đăng xuất ở thiết bị khác
        try { localStorage.removeItem(USER_KEY); } catch { /* ignore */ }
        goLogin();
      } else if (fbUser) {
        user = fbUser;
        renderUser();
      }
    });
  }

  async function signOut() {
    try { await window.LeafAuth?.signOut(); } catch { /* vẫn đăng xuất cục bộ */ }
    try {
      localStorage.removeItem(USER_KEY);
      sessionStorage.removeItem('leaf_chat_v2');
    } catch { /* ignore */ }
    location.replace(LOGIN_URL);
  }

  // ------------------------------------------------------------------
  // Thanh ứng dụng (chèn đồng bộ để không nháy layout)
  // ------------------------------------------------------------------
  const TITLES = {
    history: 'Lịch sử quét',
    library: 'Thư viện bệnh',
    disease: 'Chi tiết bệnh',
    treatment: 'Phác đồ điều trị',
    handbook: 'Cẩm nang IPM',
    about: 'Giới thiệu dự án'
  };
  const isActive = (id) => (id === page ? ' aria-current="page"' : '');

  const appbarHtml = `
    <a class="visually-hidden" href="#main">Bỏ qua thanh điều hướng</a>
    <header class="appbar" id="appbar">
      <div class="appbar-inner">
        ${page === 'scan' || !TITLES[page]
          ? `<a class="brand appbar-brand" href="${HOME_URL}" aria-label="LEAF_AI — màn hình quét lá">
               <span class="brand-mark">${LEAF_MARK}</span>
               <span class="brand-name">LEAF<span>_AI</span></span>
             </a>`
          : `<a class="appbar-back" href="${HOME_URL}" aria-label="Về màn hình quét lá"><i class="bi bi-arrow-left"></i></a>
             <span class="appbar-title">${TITLES[page]}</span>`}
        <span class="appbar-spacer"></span>
        <div class="appbar-user">
          <button class="user-btn" id="userBtn" type="button" aria-haspopup="menu" aria-expanded="false" aria-controls="userMenu" aria-label="Tài khoản và menu"></button>
          <div class="user-menu" id="userMenu" role="menu" hidden>
            <div class="user-menu-head">
              <strong id="userName">Nhà vườn</strong>
              <span id="userEmail"></span>
            </div>
            <a role="menuitem" href="scan.html"${isActive('scan')}><i class="bi bi-camera"></i>Quét lá</a>
            <a role="menuitem" href="history.html"${isActive('history')}><i class="bi bi-clock-history"></i>Lịch sử quét</a>
            <a role="menuitem" href="library.html"${isActive('library')}><i class="bi bi-journal-text"></i>Thư viện bệnh</a>
            <a role="menuitem" href="handbook.html"${isActive('handbook')}><i class="bi bi-shield-check"></i>Cẩm nang IPM</a>
            <a role="menuitem" href="about.html"${isActive('about')}><i class="bi bi-info-circle"></i>Giới thiệu dự án</a>
            <button role="menuitem" type="button" id="btnInstallPwa" hidden><i class="bi bi-download"></i>Cài ứng dụng vào máy</button>
            <button role="menuitem" type="button" id="btnLogout" class="is-danger"><i class="bi bi-box-arrow-right"></i>Đăng xuất</button>
          </div>
        </div>
      </div>
    </header>`;
  if (!isLoginPage) document.body.insertAdjacentHTML('afterbegin', appbarHtml);

  function initials(name) {
    const parts = String(name || '').trim().split(/\s+/).filter(Boolean);
    if (!parts.length) return 'L';
    return (parts.length > 1 ? parts[0][0] + parts[parts.length - 1][0] : parts[0].slice(0, 2)).toUpperCase();
  }

  function renderUser() {
    const btn = document.getElementById('userBtn');
    if (!btn || !user) return;
    const name = user.display_name || user.username || (user.email || '').split('@')[0] || 'Nhà vườn';
    btn.innerHTML = user.avatar_url
      ? `<img src="${escapeHtml(user.avatar_url)}" alt="" referrerpolicy="no-referrer">`
      : `<span>${escapeHtml(initials(name))}</span>`;
    document.getElementById('userName').textContent = name;
    document.getElementById('userEmail').textContent = user.email || '';
  }

  function initAppbar() {
    const appbar = document.getElementById('appbar');
    if (!appbar) return;

    // Viền dưới thanh ứng dụng khi cuộn (IntersectionObserver thay cho scroll listener)
    const sentinel = document.createElement('div');
    sentinel.style.cssText = 'position:absolute;top:0;height:1px;width:1px;';
    document.body.prepend(sentinel);
    new IntersectionObserver(([e]) => appbar.classList.toggle('is-scrolled', !e.isIntersecting)).observe(sentinel);

    // Menu tài khoản
    const btn = document.getElementById('userBtn');
    const menu = document.getElementById('userMenu');
    const setOpen = (open) => {
      menu.hidden = !open;
      btn.setAttribute('aria-expanded', String(open));
      if (open) menu.querySelector('a, button:not([hidden])')?.focus({ preventScroll: true });
    };
    btn.addEventListener('click', (e) => { e.stopPropagation(); setOpen(menu.hidden); });
    document.addEventListener('click', (e) => { if (!menu.hidden && !menu.contains(e.target)) setOpen(false); });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !menu.hidden) { setOpen(false); btn.focus(); }
    });
    document.getElementById('btnLogout').addEventListener('click', async () => {
      const ok = await confirmDialog('Bạn sẽ cần đăng nhập lại để tiếp tục quét lá.', { title: 'Đăng xuất?', okText: 'Đăng xuất' });
      if (ok) signOut();
    });
    renderUser();
  }

  // ------------------------------------------------------------------
  // Phần tử dùng chung cuối trang
  // ------------------------------------------------------------------
  const sharedHtml = `
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
    </dialog>`;

  const appFootHtml = `<p class="app-foot">Kết quả AI chỉ để tham khảo. Hỏi cán bộ bảo vệ thực vật địa phương trước khi phun thuốc.</p>`;

  const chatWidgetHtml = `
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

  function mount() {
    document.body.insertAdjacentHTML('beforeend', sharedHtml);
    if (isLoginPage) return;
    document.getElementById('main')?.insertAdjacentHTML('beforeend', appFootHtml);
    document.body.insertAdjacentHTML('beforeend', chatWidgetHtml);
    initAppbar();
    initPwa();
    initChatWidget();
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
    if (!btn) return;
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
    user: () => user,
    authReady,
    signOut,
    openChat: (q) => openChatFn(q),
    closeChat: () => closeChatFn(),
    toggleChat: () => toggleChatFn()
  };

  // Dựng phần còn lại khi DOM sẵn sàng (đặt cuối để mọi khai báo phía trên đã khởi tạo)
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();

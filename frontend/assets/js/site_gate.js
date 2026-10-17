/**
 * LEAF_AI — Cổng mật khẩu website (site-wide password gate)
 * - Nạp ĐỒNG BỘ trong <head> của mọi trang, trước style.css, để khóa nội dung ngay từ đầu (không nháy).
 * - Xác thực qua backend: POST /api/site-access/ (FastAPI). Backend không phản hồi
 *   (mất mạng / cold start) => so khớp SHA-256 cục bộ của mật khẩu đã chuẩn hóa.
 * - Chuẩn hóa giống backend: bỏ dấu, bỏ khoảng trắng, chữ thường
 *   => "thcs biên sơn 2026@" và "thcs bien son 2026@" đều mở được.
 * - Đổi mật khẩu: sửa SITE_PASSWORD trên Vercel + cập nhật OFFLINE_HASHES bên dưới.
 */
(function (global) {
  'use strict';

  const STORAGE_KEY = 'leaf_site_access';
  const OFFLINE_TTL_MS = 7 * 24 * 3600 * 1000;
  // sha256(normalize('thcs biên sơn 2026@')) = sha256('thcsbienson2026@')
  const OFFLINE_HASHES = ['1788535828a1254d14cce238b5441daad3d5f7592def9cba4261ed4ea5b6b2ce'];
  const BG_IMAGE = 'assets/images/lychee/vuon-vai-chinh-vu.webp';

  const doc = document;
  const root = doc.documentElement;

  // ---------- Tiện ích ----------
  const apiBase = () => {
    try {
      const custom = localStorage.getItem('leaf_backend_url');
      if (custom) return custom;
    } catch { /* private mode */ }
    const isLocal = ['localhost', '127.0.0.1', ''].includes(location.hostname);
    if (!isLocal || location.protocol === 'https:') return '';
    return location.port === '8000' ? '' : 'http://127.0.0.1:8000';
  };

  const normalize = (raw) =>
    String(raw || '')
      .normalize('NFD')
      .replace(/[̀-ͯ]/g, '')
      .replace(/đ/g, 'd').replace(/Đ/g, 'D')
      .toLowerCase()
      .replace(/\s+/g, '');

  async function sha256Hex(text) {
    if (!global.crypto?.subtle) return '';
    const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
    return Array.from(new Uint8Array(buf), (b) => b.toString(16).padStart(2, '0')).join('');
  }

  async function fetchWithTimeout(url, options = {}, ms = 8000) {
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), ms);
    try {
      return await fetch(url, { credentials: 'include', ...options, signal: ctrl.signal });
    } finally {
      clearTimeout(timer);
    }
  }

  const readGrant = () => {
    try {
      const g = JSON.parse(localStorage.getItem(STORAGE_KEY) || 'null');
      if (g && typeof g.exp === 'number' && g.exp > Date.now()) return g;
    } catch { /* ignore */ }
    return null;
  };
  const saveGrant = (g) => { try { localStorage.setItem(STORAGE_KEY, JSON.stringify(g)); } catch { /* ignore */ } };
  const clearGrant = () => { try { localStorage.removeItem(STORAGE_KEY); } catch { /* ignore */ } };

  // ---------- Trạng thái + Promise cho các script khác chờ ----------
  let resolveReady;
  const ready = new Promise((r) => { resolveReady = r; });
  let unlocked = !!readGrant();

  // CSS tối thiểu: khóa nội dung ngay khi <head> đang parse
  const style = doc.createElement('style');
  style.id = 'siteGateStyle';
  style.textContent = `
    html.site-locked, html.site-locked body { overflow: hidden !important; }
    html.site-locked body > :not(.site-gate) { visibility: hidden !important; }
    .site-gate { position: fixed; inset: 0; z-index: 2147483000; display: grid; place-items: center; padding: 20px;
      font-family: 'Be Vietnam Pro', system-ui, -apple-system, 'Segoe UI', sans-serif; color: #12301f;
      background: #0f3d26 url('${BG_IMAGE}') center / cover no-repeat; }
    .site-gate::before { content: ''; position: absolute; inset: 0;
      background: linear-gradient(160deg, rgba(10,45,27,.82) 0%, rgba(19,92,55,.62) 55%, rgba(120,30,20,.45) 100%); }
    .site-gate-card { position: relative; width: min(420px, 100%); background: rgba(255,255,255,.97); border-radius: 22px;
      padding: 32px 28px 26px; box-shadow: 0 30px 80px -24px rgba(0,0,0,.55); animation: sgIn .45s cubic-bezier(.2,.8,.2,1) both; }
    @keyframes sgIn { from { opacity: 0; transform: translateY(14px) scale(.98); } to { opacity: 1; transform: none; } }
    @keyframes sgShake { 10%,90% { transform: translateX(-1px); } 20%,80% { transform: translateX(3px); } 30%,50%,70% { transform: translateX(-6px); } 40%,60% { transform: translateX(6px); } }
    .site-gate-card.is-shake { animation: sgShake .45s both; }
    .site-gate-brand { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
    .site-gate-mark { width: 46px; height: 46px; border-radius: 14px; background: #1e7a4c; display: grid; place-items: center; flex: none; }
    .site-gate-mark svg { width: 26px; height: 26px; }
    .site-gate-name { font-weight: 800; font-size: 1.25rem; letter-spacing: -.02em; line-height: 1.1; }
    .site-gate-name span { color: #1e7a4c; }
    .site-gate-sub { font-size: .8125rem; color: #4a6354; }
    .site-gate h1 { font-size: 1.35rem; margin: 0 0 6px; letter-spacing: -.02em; line-height: 1.25; }
    .site-gate p { margin: 0 0 18px; color: #4a6354; font-size: .9rem; line-height: 1.55; }
    .site-gate label { display: block; font-size: .8125rem; font-weight: 600; margin-bottom: 6px; }
    .site-gate-field { position: relative; }
    .site-gate-field input { width: 100%; box-sizing: border-box; padding: 13px 48px 13px 42px; border: 1.5px solid #b9cdb5; border-radius: 14px;
      font: inherit; font-size: 1rem; color: #12301f; background: #f7faf5; outline: none; transition: border-color .15s, box-shadow .15s; }
    .site-gate-field input:focus { border-color: #1e7a4c; box-shadow: 0 0 0 4px rgba(30,122,76,.15); background: #fff; }
    .site-gate-field input[aria-invalid="true"] { border-color: #d4452a; }
    .site-gate-field .sg-ico { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); color: #6f8476; font-size: 1.05rem; }
    .site-gate-eye { position: absolute; right: 6px; top: 50%; transform: translateY(-50%); width: 40px; height: 40px; border: 0; border-radius: 10px;
      background: transparent; color: #4a6354; cursor: pointer; font-size: 1.1rem; }
    .site-gate-eye:hover { background: #eef7eb; }
    .site-gate-error { min-height: 20px; margin: 8px 0 4px; font-size: .8125rem; color: #b5361e; }
    .site-gate-btn { width: 100%; min-height: 50px; border: 0; border-radius: 999px; background: #1e7a4c; color: #fff; font-family: inherit; font-weight: 600; font-size: 1rem; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; gap: 8px; transition: background .15s; }
    .site-gate-btn:hover { background: #135c37; }
    .site-gate-btn:disabled { opacity: .65; cursor: progress; }
    .site-gate-hint { margin-top: 14px; font-size: .75rem; color: #6f8476; text-align: center; }
    .site-gate-credit { position: absolute; right: 12px; bottom: 10px; font-size: 10px; color: rgba(255,255,255,.7); }
    html.site-unlocking .site-gate { animation: sgOut .35s ease forwards; }
    @keyframes sgOut { to { opacity: 0; visibility: hidden; } }
    @media (prefers-reduced-motion: reduce) { .site-gate-card, html.site-unlocking .site-gate { animation: none; } }
  `;
  doc.head.appendChild(style);

  if (unlocked) {
    resolveReady(true);
  } else {
    root.classList.add('site-locked');
  }

  // ---------- Xác thực ----------
  async function verifyPassword(password) {
    try {
      const res = await fetchWithTimeout(`${apiBase()}/api/site-access/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.success) {
        if (data.enabled === false) return { ok: true, grant: { exp: Date.now() + OFFLINE_TTL_MS, mode: 'disabled' } };
        return { ok: true, grant: { token: data.token, exp: data.expires_at * 1000, mode: 'server' } };
      }
      if (res.status === 401 || res.status === 429) return { ok: false, error: data.error };
      // 404 / 5xx: backend chưa có endpoint hoặc lỗi -> rơi xuống kiểm tra cục bộ
    } catch { /* mất mạng / timeout */ }

    const hash = await sha256Hex(normalize(password));
    if (hash && OFFLINE_HASHES.includes(hash)) {
      return { ok: true, grant: { exp: Date.now() + OFFLINE_TTL_MS, mode: 'offline' } };
    }
    return { ok: false, error: 'Mật khẩu không đúng. Vui lòng thử lại.' };
  }

  // Phiên đã mở bằng token máy chủ: kiểm tra nền, nếu mật khẩu đã bị đổi thì khóa lại.
  async function revalidate() {
    const g = readGrant();
    if (!g || g.mode !== 'server') return;
    try {
      const res = await fetchWithTimeout(`${apiBase()}/api/site-access/`, { headers: { 'X-Site-Access': g.token } }, 6000);
      if (!res.ok) return;
      const data = await res.json();
      if (data.enabled !== false && data.unlocked === false) lock();
    } catch { /* offline: giữ nguyên */ }
  }

  // ---------- Giao diện ----------
  const LEAF_SVG = `<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M19.5 4.5c-7.2.1-12.6 3.4-14 9.2-.5 2 .1 3.8 1.3 5 3.6-4.6 7-7.1 10.2-8.6-2.8 2.1-5.6 5-7.8 8.6 1.1.4 2.4.4 3.7 0 5.1-1.7 7-7.3 6.6-14.2Z" fill="#fff"/></svg>`;

  function renderGate() {
    if (doc.getElementById('siteGate')) return;
    const wrap = doc.createElement('div');
    wrap.className = 'site-gate';
    wrap.id = 'siteGate';
    wrap.setAttribute('role', 'dialog');
    wrap.setAttribute('aria-modal', 'true');
    wrap.setAttribute('aria-labelledby', 'siteGateTitle');
    wrap.innerHTML = `
      <form class="site-gate-card" id="siteGateForm" novalidate>
        <div class="site-gate-brand">
          <span class="site-gate-mark">${LEAF_SVG}</span>
          <div>
            <div class="site-gate-name">LEAF<span>_AI</span></div>
            <div class="site-gate-sub">Bác sĩ lá vải thiều Lục Ngạn</div>
          </div>
        </div>
        <h1 id="siteGateTitle">Nhập mật khẩu để vào website</h1>
        <p>Website đang được bảo vệ cho buổi trình bày dự án. Vui lòng nhập mật khẩu được cung cấp.</p>
        <label for="siteGatePass">Mật khẩu</label>
        <div class="site-gate-field">
          <i class="bi bi-lock sg-ico" aria-hidden="true"></i>
          <input type="password" id="siteGatePass" name="password" autocomplete="current-password" required
                 autocapitalize="off" spellcheck="false" placeholder="Nhập mật khẩu" aria-describedby="siteGateError">
          <button type="button" class="site-gate-eye" id="siteGateEye" aria-label="Hiện mật khẩu"><i class="bi bi-eye"></i></button>
        </div>
        <div class="site-gate-error" id="siteGateError" role="alert" aria-live="assertive"></div>
        <button type="submit" class="site-gate-btn" id="siteGateBtn"><i class="bi bi-unlock"></i><span>Vào website</span></button>
        <div class="site-gate-hint">Có thể gõ có dấu hoặc không dấu.</div>
      </form>
      <span class="site-gate-credit">Ảnh: Forest &amp; Kim Starr, CC BY 3.0</span>`;
    doc.body.appendChild(wrap);

    const form = wrap.querySelector('#siteGateForm');
    const input = wrap.querySelector('#siteGatePass');
    const btn = wrap.querySelector('#siteGateBtn');
    const err = wrap.querySelector('#siteGateError');
    const eye = wrap.querySelector('#siteGateEye');

    eye.addEventListener('click', () => {
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      eye.setAttribute('aria-label', show ? 'Ẩn mật khẩu' : 'Hiện mật khẩu');
      eye.innerHTML = `<i class="bi ${show ? 'bi-eye-slash' : 'bi-eye'}"></i>`;
      input.focus();
    });
    input.addEventListener('input', () => { err.textContent = ''; input.removeAttribute('aria-invalid'); });

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const value = input.value;
      if (!value.trim()) {
        err.textContent = 'Vui lòng nhập mật khẩu.';
        input.setAttribute('aria-invalid', 'true');
        input.focus();
        return;
      }
      btn.disabled = true;
      btn.querySelector('span').textContent = 'Đang kiểm tra...';
      const result = await verifyPassword(value);
      if (result.ok) {
        saveGrant(result.grant);
        unlock();
        return;
      }
      btn.disabled = false;
      btn.querySelector('span').textContent = 'Vào website';
      err.textContent = result.error || 'Mật khẩu không đúng. Vui lòng thử lại.';
      input.setAttribute('aria-invalid', 'true');
      input.select();
      form.classList.remove('is-shake');
      void form.offsetWidth; // khởi động lại animation rung
      form.classList.add('is-shake');
    });

    requestAnimationFrame(() => input.focus());
  }

  function unlock() {
    unlocked = true;
    const gate = doc.getElementById('siteGate');
    root.classList.remove('site-locked');
    resolveReady(true);
    if (!gate) return;
    root.classList.add('site-unlocking');
    gate.addEventListener('animationend', () => { gate.remove(); root.classList.remove('site-unlocking'); }, { once: true });
    // Dự phòng khi trình duyệt tắt animation
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) { gate.remove(); root.classList.remove('site-unlocking'); }
  }

  function lock() {
    clearGrant();
    unlocked = false;
    root.classList.add('site-locked');
    if (doc.body) renderGate();
    else doc.addEventListener('DOMContentLoaded', renderGate, { once: true });
  }

  if (!unlocked) {
    if (doc.readyState === 'loading') doc.addEventListener('DOMContentLoaded', renderGate, { once: true });
    else renderGate();
  } else {
    // Kiểm tra nền sau khi trang tải xong, không chặn hiển thị
    global.addEventListener('load', revalidate, { once: true });
  }

  global.LeafSiteGate = {
    ready,
    isUnlocked: () => unlocked,
    lock
  };
})(window);

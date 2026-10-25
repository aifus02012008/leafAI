/**
 * LEAF_AI — Firebase Authentication Client
 * Cung cấp xác thực đăng nhập: Google OAuth (Google Sign-In), Email & Password và quản lý phiên.
 */
(function (global) {
  'use strict';

  const FIREBASE_CONFIG = {
    apiKey: "AIzaSyBjmtw_sJSM6IMwJqJkwRhmbLsgAsYJkmQ",
    authDomain: "leaf-ai-app-2026.firebaseapp.com",
    projectId: "leaf-ai-app-2026",
    storageBucket: "leaf-ai-app-2026.firebasestorage.app",
    messagingSenderId: "985474944909",
    appId: "1:985474944909:web:d3ab39b458d3d8b492b7c4"
  };

  const APP_URL = 'https://www.gstatic.com/firebasejs/10.14.1/firebase-app.js';
  const AUTH_URL = 'https://www.gstatic.com/firebasejs/10.14.1/firebase-auth.js';

  let firebaseAuth = null;
  let authModules = null;
  let initPromise = null;
  const authStateListeners = [];
  // Trạng thái đăng nhập đầu tiên Firebase khôi phục được (user | null); undefined = SDK không tải được (offline)
  let resolveReady;
  const readyPromise = new Promise((r) => { resolveReady = r; });
  let readySettled = false;
  const settleReady = (v) => { if (!readySettled) { readySettled = true; resolveReady(v); } };

  async function getAuthInstance() {
    if (firebaseAuth && authModules) return { auth: firebaseAuth, mod: authModules };
    if (initPromise) return initPromise;

    initPromise = (async () => {
      try {
        const { initializeApp, getApps, getApp } = await import(APP_URL);
        const {
          getAuth,
          GoogleAuthProvider,
          signInWithPopup,
          signInWithRedirect,
          getRedirectResult,
          signInWithEmailAndPassword,
          createUserWithEmailAndPassword,
          updateProfile,
          sendPasswordResetEmail,
          signOut,
          onAuthStateChanged
        } = await import(AUTH_URL);

        const app = getApps().length ? getApp() : initializeApp(FIREBASE_CONFIG);
        firebaseAuth = getAuth(app);
        authModules = {
          GoogleAuthProvider,
          signInWithPopup,
          signInWithRedirect,
          getRedirectResult,
          signInWithEmailAndPassword,
          createUserWithEmailAndPassword,
          updateProfile,
          sendPasswordResetEmail,
          signOut,
          onAuthStateChanged
        };

        // Lắng nghe sự kiện thay đổi phiên đăng nhập
        onAuthStateChanged(firebaseAuth, (user) => {
          const formatted = formatUser(user);
          if (formatted) {
            localStorage.setItem('leaf_last_user', JSON.stringify(formatted));
          }
          settleReady(formatted);
          authStateListeners.forEach((fn) => {
            try { fn('AUTH_STATE_CHANGE', formatted, user); } catch (err) { console.error(err); }
          });
        });

        // Bắt kết quả nếu trước đó dùng redirect
        getRedirectResult(firebaseAuth).then((result) => {
          if (result && result.user) {
            const formatted = formatUser(result.user);
            localStorage.setItem('leaf_last_user', JSON.stringify(formatted));
          }
        }).catch((err) => {
          console.warn('[LEAF_AI] Firebase getRedirectResult notice:', err);
        });

        return { auth: firebaseAuth, mod: authModules };
      } catch (err) {
        console.warn('[LEAF_AI] Không thể khởi tạo Firebase Auth SDK:', err);
        settleReady(undefined);
        return null;
      }
    })();

    return initPromise;
  }

  function formatUser(user) {
    if (!user) return null;
    const email = user.email || '';
    const name = user.displayName || email.split('@')[0] || 'Nông dân Lục Ngạn';
    return {
      id: user.uid,
      uid: user.uid,
      email: email,
      username: name,
      display_name: name,
      avatar_url: user.photoURL || null,
      is_authenticated: true,
      provider: user.providerData && user.providerData[0] ? user.providerData[0].providerId : 'firebase'
    };
  }

  const LeafAuth = {
    isConfigured: true,
    provider: 'firebase',

    /** Chờ Firebase khôi phục phiên: user | null; undefined nếu SDK không tải được (vd mất mạng). Tối đa 8 giây. */
    whenReady(timeoutMs = 8000) {
      return Promise.race([readyPromise, new Promise((r) => setTimeout(() => r(undefined), timeoutMs))]);
    },

    async resetPassword(email) {
      const instance = await getAuthInstance();
      if (!instance) throw new Error('Chưa kết nối được máy chủ đăng nhập. Kiểm tra mạng rồi thử lại.');
      try {
        await instance.mod.sendPasswordResetEmail(instance.auth, String(email || '').trim());
        return { success: true };
      } catch (err) {
        throw new Error({
          'auth/invalid-email': 'Email không đúng định dạng.',
          'auth/missing-email': 'Nhập email trước khi lấy lại mật khẩu.',
          'auth/user-not-found': 'Không có tài khoản nào dùng email này.',
          'auth/too-many-requests': 'Bạn yêu cầu quá nhiều lần. Thử lại sau ít phút.'
        }[err.code] || 'Không gửi được email đặt lại mật khẩu.');
      }
    },

    async getCurrentUser() {
      // 1. Kiểm tra từ SDK
      const instance = await getAuthInstance();
      if (instance && instance.auth && instance.auth.currentUser) {
        const u = formatUser(instance.auth.currentUser);
        localStorage.setItem('leaf_last_user', JSON.stringify(u));
        return u;
      }
      // 2. Fallback localStorage
      try {
        const local = localStorage.getItem('leaf_last_user');
        if (local) {
          const u = JSON.parse(local);
          if (u && u.is_authenticated) return u;
        }
      } catch {}
      return null;
    },

    async signInWithGoogle() {
      const instance = await getAuthInstance();
      if (!instance) {
        throw new Error('Chưa kết nối được Firebase Auth. Vui lòng kiểm tra kết nối mạng.');
      }
      const { auth, mod } = instance;
      const provider = new mod.GoogleAuthProvider();
      provider.setCustomParameters({ prompt: 'select_account' });

      try {
        const res = await mod.signInWithPopup(auth, provider);
        const user = formatUser(res.user);
        if (user) {
          localStorage.setItem('leaf_last_user', JSON.stringify(user));
        }
        return { user, credential: res };
      } catch (err) {
        console.error('[LEAF_AI] Firebase Google Sign-In error:', err);
        if (err.code === 'auth/popup-blocked') {
          await mod.signInWithRedirect(auth, provider);
          return null;
        }
        const friendlyMessage = {
          'auth/configuration-not-found': 'Dự án Firebase mới chưa kích hoạt Authentication. Bạn chỉ cần vào Firebase Console > Authentication bấm "Get started" để bật hệ thống xác thực.',
          'auth/operation-not-allowed': 'Phương thức đăng nhập Google chưa được bật trong Firebase Console > Authentication > Sign-in method.',
          'auth/unauthorized-domain': 'Tên miền chưa được cấp phép trong Firebase Auth. Vui lòng thêm domain vào Authorized Domains trong Settings.',
          'auth/popup-blocked': 'Trình duyệt đang chặn cửa sổ Popup. Vui lòng cho phép popup để đăng nhập.',
          'auth/popup-closed-by-user': 'Hộp thoại đăng nhập Google đã bị đóng trước khi hoàn tất.',
          'auth/cancelled-popup-request': 'Thao tác đăng nhập Google bị hủy do có yêu cầu mới.',
          'auth/network-request-failed': 'Lỗi kết nối mạng khi liên hệ máy chủ Google.'
        }[err.code] || (err.message || 'Đăng nhập Google thất bại.');
        throw new Error(friendlyMessage);
      }
    },

    async signInWithEmail(email, password) {
      const instance = await getAuthInstance();
      if (!instance) {
        throw new Error('Chưa kết nối được Firebase Auth. Vui lòng thử lại sau.');
      }
      const { auth, mod } = instance;
      try {
        const res = await mod.signInWithEmailAndPassword(auth, email.trim(), password);
        const user = formatUser(res.user);
        if (user) {
          localStorage.setItem('leaf_last_user', JSON.stringify(user));
        }
        return { user, credential: res };
      } catch (err) {
        const friendlyMessage = {
          'auth/invalid-credential': 'Email hoặc mật khẩu không chính xác.',
          'auth/operation-not-allowed': 'Đăng nhập bằng email chưa được bật trong Firebase Console > Authentication > Sign-in method.',
          'auth/network-request-failed': 'Mất kết nối mạng. Kiểm tra mạng rồi thử lại.',
          'auth/user-not-found': 'Tài khoản không tồn tại. Vui lòng đăng ký tài khoản mới.',
          'auth/wrong-password': 'Mật khẩu không chính xác.',
          'auth/invalid-email': 'Định dạng email không hợp lệ.',
          'auth/too-many-requests': 'Đăng nhập sai quá nhiều lần. Vui lòng thử lại sau ít phút.'
        }[err.code] || (err.message || 'Đăng nhập thất bại.');
        throw new Error(friendlyMessage);
      }
    },

    async signUpWithEmail(email, password, username) {
      const instance = await getAuthInstance();
      if (!instance) {
        throw new Error('Chưa kết nối được Firebase Auth. Vui lòng thử lại sau.');
      }
      const { auth, mod } = instance;
      try {
        const res = await mod.createUserWithEmailAndPassword(auth, email.trim(), password);
        if (username && res.user) {
          await mod.updateProfile(res.user, { displayName: username.trim() }).catch(() => {});
        }
        const user = formatUser(res.user);
        if (user) {
          if (username) {
            user.username = username.trim();
            user.display_name = username.trim();
          }
          localStorage.setItem('leaf_last_user', JSON.stringify(user));
        }
        return { user, credential: res };
      } catch (err) {
        const friendlyMessage = {
          'auth/email-already-in-use': 'Email này đã được đăng ký. Vui lòng chuyển sang tab Đăng nhập.',
          'auth/weak-password': 'Mật khẩu quá yếu (yêu cầu tối thiểu 6 ký tự).',
          'auth/invalid-email': 'Địa chỉ email không đúng định dạng.'
        }[err.code] || (err.message || 'Đăng ký thất bại.');
        throw new Error(friendlyMessage);
      }
    },

    async signOut() {
      localStorage.removeItem('leaf_last_user');
      const instance = await getAuthInstance();
      if (instance && instance.auth) {
        try {
          await instance.mod.signOut(instance.auth);
        } catch (e) {
          console.warn('[LEAF_AI] Firebase signOut notice:', e);
        }
      }
      return { success: true };
    },

    onAuthStateChange(listener) {
      if (typeof listener === 'function') {
        authStateListeners.push(listener);
      }
    }
  };

  global.LeafAuth = LeafAuth;
  getAuthInstance();
})(typeof window !== 'undefined' ? window : this);

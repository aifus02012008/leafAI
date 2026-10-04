/**
 * LEAF_AI — Supabase Authentication Client
 * Cung cấp xác thực đăng nhập: Google OAuth, Email & Password và quản lý phiên.
 */
(function (global) {
  'use strict';

  const SUPABASE_URL = 'https://ribpggqkojqghutyverv.supabase.co';
  const SUPABASE_ANON_KEY = 'sb_publishable_XQdN7Y6Z7QKbssbp4UbBbg_96uLznEh';
  const CDN_URL = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/+esm';

  let supabaseClient = null;
  let initPromise = null;
  const authStateListeners = [];

  /** Khởi tạo Supabase client */
  async function getClient() {
    if (supabaseClient) return supabaseClient;
    if (initPromise) return initPromise;

    initPromise = (async () => {
      try {
        const { createClient } = await import(CDN_URL);
        supabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
          auth: {
            persistSession: true,
            autoRefreshToken: true,
            detectSessionInUrl: true
          }
        });

        // Lắng nghe sự kiện thay đổi phiên đăng nhập
        supabaseClient.auth.onAuthStateChange((event, session) => {
          const formattedUser = formatUser(session ? session.user : null);
          authStateListeners.forEach((fn) => {
            try { fn(event, formattedUser, session); } catch (err) { console.error(err); }
          });
        });

        return supabaseClient;
      } catch (err) {
        console.warn('[LEAF_AI] Không thể nạp Supabase client từ CDN:', err);
        return null;
      }
    })();

    return initPromise;
  }

  /** Chuẩn hóa thông tin người dùng từ Supabase User */
  function formatUser(rawUser) {
    if (!rawUser) return null;
    const meta = rawUser.user_metadata || {};
    const email = rawUser.email || '';
    const name = meta.full_name || meta.name || meta.username || email.split('@')[0] || 'Nông dân';
    const avatar = meta.avatar_url || meta.picture || null;
    return {
      id: rawUser.id,
      email: email,
      username: name,
      display_name: name,
      avatar_url: avatar,
      is_authenticated: true,
      provider: rawUser.app_metadata?.provider || 'email'
    };
  }

  const LeafAuth = {
    isConfigured: true,

    /** Lấy phiên đăng nhập hiện tại */
    async getCurrentUser() {
      // 1. Kiểm tra session trong Supabase client
      const client = await getClient();
      if (client) {
        try {
          const { data, error } = await client.auth.getSession();
          if (!error && data?.session?.user) {
            const user = formatUser(data.session.user);
            localStorage.setItem('leaf_last_user', JSON.stringify(user));
            return user;
          }
        } catch (e) {
          console.warn('[LEAF_AI] Lỗi lấy session Supabase:', e);
        }
      }

      // 2. Fallback nếu đã lưu cục bộ trong phiên trước (khi mất mạng ngoại tuyến)
      try {
        const local = localStorage.getItem('leaf_last_user');
        if (local) {
          const u = JSON.parse(local);
          if (u && u.is_authenticated) return u;
        }
      } catch {}

      return null;
    },

    /** Đăng nhập bằng tài khoản Google */
    async signInWithGoogle() {
      const client = await getClient();
      if (!client) {
        throw new Error('Chưa kết nối được máy chủ Supabase. Vui lòng kiểm tra kết nối mạng.');
      }

      // Giữ trang hiện tại làm callback redirect
      const currentUrl = window.location.href.split('#')[0];
      const { data, error } = await client.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: currentUrl,
          queryParams: {
            access_type: 'offline',
            prompt: 'consent'
          }
        }
      });

      if (error) {
        throw new Error(error.message || 'Đăng nhập Google thất bại');
      }
      return data;
    },

    /** Đăng nhập bằng Email và Mật khẩu */
    async signInWithEmail(email, password) {
      const client = await getClient();
      if (!client) {
        throw new Error('Chưa kết nối được máy chủ Supabase. Vui lòng thử lại sau.');
      }

      const { data, error } = await client.auth.signInWithPassword({
        email: email.trim(),
        password: password
      });

      if (error) {
        const msg = error.message.includes('Invalid login credentials')
          ? 'Email hoặc mật khẩu không chính xác.'
          : (error.message || 'Đăng nhập thất bại.');
        throw new Error(msg);
      }

      const user = formatUser(data.user);
      localStorage.setItem('leaf_last_user', JSON.stringify(user));
      return { user, session: data.session };
    },

    /** Đăng ký tài khoản mới bằng Email và Mật khẩu */
    async signUpWithEmail(email, password, username) {
      const client = await getClient();
      if (!client) {
        throw new Error('Chưa kết nối được máy chủ Supabase. Vui lòng thử lại sau.');
      }

      const { data, error } = await client.auth.signUp({
        email: email.trim(),
        password: password,
        options: {
          data: {
            username: username.trim(),
            full_name: username.trim()
          }
        }
      });

      if (error) {
        const msg = error.message.includes('User already registered')
          ? 'Email này đã được đăng ký. Vui lòng chuyển sang tab Đăng nhập.'
          : (error.message || 'Đăng ký thất bại.');
        throw new Error(msg);
      }

      const user = formatUser(data.user);
      if (user) {
        localStorage.setItem('leaf_last_user', JSON.stringify(user));
      }
      return { user, session: data.session };
    },

    /** Đăng xuất khỏi hệ thống */
    async signOut() {
      localStorage.removeItem('leaf_last_user');
      const client = await getClient();
      if (client) {
        try {
          await client.auth.signOut();
        } catch (e) {
          console.warn('[LEAF_AI] Supabase signOut warning:', e);
        }
      }
      return { success: true };
    },

    /** Lắng nghe thay đổi trạng thái đăng nhập */
    onAuthStateChange(listener) {
      if (typeof listener === 'function') {
        authStateListeners.push(listener);
      }
    }
  };

  global.LeafAuth = LeafAuth;
  // Khởi động sớm client để bắt redirect hash nếu có
  getClient();
})(typeof window !== 'undefined' ? window : this);

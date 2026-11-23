/* LEAF_AI service worker: offline app shell + Web Push notifications. */
const SHELL_CACHE = 'leafai-shell-v1';
const ASSET_CACHE = 'leafai-assets-v1';
const SCOPE = self.registration.scope; // e.g. https://host/leaf_ai2/
const INDEX_URL = new URL('index.html', SCOPE).href;

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(SHELL_CACHE).then((c) => c.add(INDEX_URL)).catch(() => undefined));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => ![SHELL_CACHE, ASSET_CACHE].includes(k)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin || url.pathname.includes('/api/')) return; // never cache API data

  // App navigations: network first, fall back to the cached shell when offline.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(SHELL_CACHE).then((c) => c.put(INDEX_URL, copy)).catch(() => undefined);
          }
          return res;
        })
        .catch(() => caches.match(INDEX_URL))
    );
    return;
  }

  // Hashed build assets are immutable: cache first.
  if (url.pathname.includes('/assets/')) {
    event.respondWith(
      caches.match(req).then(
        (hit) =>
          hit ||
          fetch(req).then((res) => {
            if (res.ok) {
              const copy = res.clone();
              caches.open(ASSET_CACHE).then((c) => c.put(req, copy)).catch(() => undefined);
            }
            return res;
          })
      )
    );
  }
});

/** Only in-app relative links are opened from a notification. */
function safeTarget(link) {
  if (typeof link !== 'string' || !link.startsWith('/') || link.startsWith('//') || link.includes('\\')) return SCOPE;
  try {
    const target = new URL(link.replace(/^\/+/, ''), SCOPE).href;
    return target.startsWith(SCOPE) ? target : SCOPE;
  } catch {
    return SCOPE;
  }
}

self.addEventListener('push', (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch {
    data = { title: 'LEAF_AI', body: event.data ? event.data.text() : '' };
  }
  const title = data.title || 'LEAF_AI';
  event.waitUntil(
    self.registration.showNotification(title, {
      body: data.body || '',
      icon: new URL('icon-192.png', SCOPE).href,
      badge: new URL('badge-96.png', SCOPE).href,
      tag: data.tag || 'leafai',
      lang: 'vi',
      data: { url: safeTarget(data.link) },
    })
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const target = (event.notification.data && event.notification.data.url) || SCOPE;
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then((wins) => {
      for (const w of wins) {
        if (w.url.startsWith(SCOPE) && 'focus' in w) {
          w.navigate(target);
          return w.focus();
        }
      }
      return self.clients.openWindow(target);
    })
  );
});

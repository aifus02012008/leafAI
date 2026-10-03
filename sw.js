/**
 * LEAF_AI Service Worker (PWA)
 * - Trang & tài nguyên tĩnh: cache sẵn để mở được khi mất sóng ngoài ruộng.
 * - Điều hướng: network-first, rớt mạng thì lấy bản đã cache.
 * - Gọi API (/api/, /health/) không cache.
 */
const CACHE_NAME = 'leaf-ai-v2.0.0';
const STATIC_ASSETS = [
  './',
  './index.html',
  './scan.html',
  './library.html',
  './disease.html',
  './handbook.html',
  './history.html',
  './assistant.html',
  './about.html',
  './manifest.json',
  './assets/css/style.css',
  './assets/js/core.js',
  './assets/js/disease_data.js',
  './assets/js/api.js',
  './assets/js/canvas_render.js',
  './assets/js/camera.js',
  './assets/js/pages/landing.js',
  './assets/js/pages/scan.js',
  './assets/js/pages/library.js',
  './assets/js/pages/disease.js',
  './assets/js/pages/handbook.js',
  './assets/js/pages/history.js',
  './assets/js/pages/assistant.js',
  './assets/images/icon-192.png',
  './assets/images/icon-512.png',
  './assets/images/early_blight.svg',
  './assets/images/late_blight.svg',
  './assets/images/bacterial_spot.svg',
  './assets/images/septoria_leaf_spot.svg',
  './assets/images/leaf_mold.svg',
  './assets/images/powdery_mildew.svg',
  './assets/samples/sample_early_blight.jpg',
  './assets/samples/sample_late_blight.jpg',
  './assets/samples/sample_bacterial_spot.jpg',
  './assets/samples/sample_septoria.jpg',
  './assets/samples/sample_healthy_leaf.jpg'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .catch((err) => console.warn('[LEAF_AI SW] Cache warning:', err))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.pathname.includes('/api/') || url.pathname.endsWith('/health/')) return;

  // Điều hướng trang: network-first
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE_NAME).then((c) => c.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req, { ignoreSearch: true }).then((r) => r || caches.match('./index.html')))
    );
    return;
  }

  // Tài nguyên tĩnh (kể cả font/icon CDN): stale-while-revalidate
  event.respondWith(
    caches.match(req).then((cached) => {
      const network = fetch(req)
        .then((res) => {
          if (res && (res.ok || res.type === 'opaque')) {
            const copy = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(req, copy));
          }
          return res;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});

/** Register the service worker (production builds only, so dev hot-reload is unaffected). */
export function registerServiceWorker(): void {
  if (!import.meta.env.PROD || !('serviceWorker' in navigator)) return;
  const base = import.meta.env.BASE_URL || '/';
  window.addEventListener('load', () => {
    navigator.serviceWorker.register(`${base}sw.js`, { scope: base }).catch(() => {
      /* offline support and push are optional; the app works without them */
    });
  });
}

/** Wait for an active registration (needed before subscribing to push). */
export async function getServiceWorkerRegistration(): Promise<ServiceWorkerRegistration | null> {
  if (!('serviceWorker' in navigator)) return null;
  const base = import.meta.env.BASE_URL || '/';
  const existing = await navigator.serviceWorker.getRegistration(base);
  if (existing) return existing;
  try {
    return await navigator.serviceWorker.register(`${base}sw.js`, { scope: base });
  } catch {
    return null;
  }
}

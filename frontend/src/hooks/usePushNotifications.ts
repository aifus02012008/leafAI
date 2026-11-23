import { useCallback, useEffect, useState } from 'react';
import { apiGetPushConfig, apiSubscribePush, apiUnsubscribePush } from '../api/farms';
import { getServiceWorkerRegistration } from '../pwa/registerServiceWorker';

export type PushState = 'loading' | 'unsupported' | 'server-disabled' | 'denied' | 'off' | 'on';

function urlBase64ToUint8Array(base64: string): Uint8Array {
  const padding = '='.repeat((4 - (base64.length % 4)) % 4);
  const raw = atob((base64 + padding).replace(/-/g, '+').replace(/_/g, '/'));
  return Uint8Array.from(raw, (c) => c.charCodeAt(0));
}

const supported = () =>
  typeof window !== 'undefined' && 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;

/** Web Push opt-in for this browser. */
export function usePushNotifications() {
  const [state, setState] = useState<PushState>('loading');
  const [publicKey, setPublicKey] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      if (!supported()) return active && setState('unsupported');
      try {
        const cfg = await apiGetPushConfig();
        if (!active) return;
        if (!cfg.enabled || !cfg.public_key) return setState('server-disabled');
        setPublicKey(cfg.public_key);
        if (Notification.permission === 'denied') return setState('denied');
        const reg = await getServiceWorkerRegistration();
        const sub = reg ? await reg.pushManager.getSubscription() : null;
        if (active) setState(sub ? 'on' : 'off');
      } catch {
        if (active) setState('server-disabled');
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  const enable = useCallback(async () => {
    if (!publicKey) return;
    setBusy(true);
    try {
      const permission = await Notification.requestPermission();
      if (permission !== 'granted') {
        setState(permission === 'denied' ? 'denied' : 'off');
        return;
      }
      const reg = await getServiceWorkerRegistration();
      if (!reg) throw new Error('no service worker');
      await navigator.serviceWorker.ready;
      const sub =
        (await reg.pushManager.getSubscription()) ||
        (await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(publicKey),
        }));
      await apiSubscribePush(sub.toJSON());
      setState('on');
    } finally {
      setBusy(false);
    }
  }, [publicKey]);

  const disable = useCallback(async () => {
    setBusy(true);
    try {
      const reg = await getServiceWorkerRegistration();
      const sub = reg ? await reg.pushManager.getSubscription() : null;
      if (sub) {
        await apiUnsubscribePush(sub.endpoint).catch(() => undefined);
        await sub.unsubscribe();
      }
      setState('off');
    } finally {
      setBusy(false);
    }
  }, []);

  return { state, busy, enable, disable };
}

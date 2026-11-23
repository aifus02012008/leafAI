import type { GeoPoint } from '../types';

const RADAR_SHARE_KEY = 'leafai_radar_share';

/** One-shot browser geolocation; resolves null when unavailable or denied. */
export function getCurrentPosition(timeoutMs = 8000): Promise<GeoPoint | null> {
  if (typeof navigator === 'undefined' || !navigator.geolocation) return Promise.resolve(null);
  return new Promise((resolve) => {
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => resolve(null),
      { enableHighAccuracy: false, timeout: timeoutMs, maximumAge: 10 * 60 * 1000 }
    );
  });
}

export function readRadarConsent(): boolean {
  try {
    return localStorage.getItem(RADAR_SHARE_KEY) === '1';
  } catch {
    return false;
  }
}

export function storeRadarConsent(value: boolean): void {
  try {
    localStorage.setItem(RADAR_SHARE_KEY, value ? '1' : '0');
  } catch {
    /* storage unavailable — consent simply isn't remembered */
  }
}

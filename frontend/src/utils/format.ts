import type { AreaUnit, Verdict } from '../types';

/** Today's date as YYYY-MM-DD in the user's local timezone. */
export function todayIso(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** Whole days from today until an ISO date (negative when in the past). */
export function daysUntil(isoDate: string): number {
  const [y, m, d] = isoDate.split('-').map(Number);
  const target = new Date(y, m - 1, d).getTime();
  const [ty, tm, td] = todayIso().split('-').map(Number);
  const today = new Date(ty, tm - 1, td).getTime();
  return Math.round((target - today) / 86_400_000);
}

export function formatDate(isoDate: string | null | undefined): string {
  if (!isoDate) return '—';
  const [y, m, d] = isoDate.slice(0, 10).split('-');
  return `${d}/${m}/${y}`;
}

export function formatNumber(value: number, maxFractionDigits = 1): string {
  return value.toLocaleString('vi-VN', { maximumFractionDigits: maxFractionDigits });
}

export function formatVnd(value: number): string {
  return `${Math.round(value).toLocaleString('vi-VN')} đ`;
}

export const AREA_UNIT_LABELS: Record<AreaUnit, string> = {
  m2: 'm²',
  sao_bac_bo: 'sào Bắc Bộ (360 m²)',
  sao_trung_bo: 'sào Trung Bộ (500 m²)',
  cong: 'công Nam Bộ (1.000 m²)',
  ha: 'ha',
};

export const VERDICT_META: Record<Verdict, { label: string; className: string }> = {
  effective: { label: 'Thuốc có tác dụng', className: 'bg-emerald-50 text-emerald-800 border-emerald-200' },
  unclear: { label: 'Chưa rõ — theo dõi thêm', className: 'bg-amber-50 text-amber-800 border-amber-200' },
  ineffective: { label: 'Chưa hiệu quả', className: 'bg-red-50 text-red-700 border-red-200' },
  inconclusive: { label: 'Không đo được', className: 'bg-slate-100 text-slate-700 border-slate-200' },
};

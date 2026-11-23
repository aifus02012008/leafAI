import { AlertTriangle, RefreshCw } from 'lucide-react';
import { VERDICT_META, formatNumber } from '../utils/format';
import type { FollowupResult } from '../types';

/** Before/after verdict shown after a re-photo of a treated leaf. */
export function FollowupVerdictCard({ result }: { result: FollowupResult }) {
  const meta = VERDICT_META[result.verdict];
  const pct = (v: number | null) => (v === null ? '—' : `${formatNumber(v)}%`);

  return (
    <div className="p-4 rounded-2xl bg-white border border-[#E2EFE7] space-y-3 text-xs" aria-live="polite">
      <div className="flex items-center justify-between gap-2">
        <span className="font-bold text-slate-900">Đánh giá hiệu quả điều trị</span>
        <span className={`px-2.5 py-0.5 rounded-full border font-bold ${meta.className}`}>{meta.label}</span>
      </div>

      <div className="grid grid-cols-3 gap-2 text-center">
        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
          <span className="block text-[10px] text-slate-500">Vết bệnh trước</span>
          <span className="font-mono font-extrabold text-slate-900">{pct(result.severity_before)}</span>
        </div>
        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
          <span className="block text-[10px] text-slate-500">Vết bệnh sau</span>
          <span className="font-mono font-extrabold text-slate-900">{pct(result.severity_after)}</span>
        </div>
        <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200">
          <span className="block text-[10px] text-slate-500">Thay đổi</span>
          <span className="font-mono font-extrabold text-slate-900">
            {result.relative_change === null ? '—' : `${result.relative_change > 0 ? '+' : ''}${formatNumber(result.relative_change * 100, 0)}%`}
          </span>
        </div>
      </div>

      <p className="text-slate-700 leading-relaxed">{result.message}</p>

      {result.checklist.length > 0 && (
        <div className="p-3 rounded-xl bg-amber-50/70 border border-amber-200 space-y-1.5">
          <span className="font-bold text-amber-900 flex items-center gap-1.5">
            <AlertTriangle size={13} /> Kiểm tra trước khi đổi thuốc
          </span>
          <ol className="list-decimal pl-4 space-y-1 text-slate-700">
            {result.checklist.map((item) => <li key={item}>{item}</li>)}
          </ol>
        </div>
      )}

      {result.rotation_suggestions.length > 0 && (
        <div className="p-3 rounded-xl bg-[#F0FDF4] border border-emerald-200 space-y-1.5">
          <span className="font-bold text-[#14532D] flex items-center gap-1.5">
            <RefreshCw size={13} /> Hoạt chất khác nhóm tác động nên luân phiên
          </span>
          <ul className="flex flex-wrap gap-1.5">
            {result.rotation_suggestions.map((a) => (
              <li key={a.code} className="px-2 py-0.5 rounded-md bg-white border border-emerald-200 font-semibold text-slate-800">
                {a.name}{a.moa_code ? ` (${a.moa_scheme} ${a.moa_code})` : ''}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

import { useState, type FormEvent } from 'react';
import { CalendarClock, Loader2 } from 'lucide-react';
import { apiCalcHarvest } from '../api/treatments';
import { DoseCalculator } from '../components/DoseCalculator';
import { showToast } from '../components/Toast';
import { formatDate, todayIso } from '../utils/format';
import type { HarvestResult } from '../types';

function HarvestCalculator() {
  const [appliedOn, setAppliedOn] = useState(todayIso());
  const [phi, setPhi] = useState('');
  const [result, setResult] = useState<HarvestResult | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const days = Number(phi);
    if (phi.trim() === '' || !Number.isInteger(days) || days < 0 || days > 365) {
      showToast('error', 'Nhập thời gian cách ly trên nhãn (số ngày, 0–365).');
      return;
    }
    setLoading(true);
    try {
      setResult(await apiCalcHarvest([{ applied_on: appliedOn, phi_days: days }]));
    } catch {
      showToast('error', 'Không tính được ngày thu hoạch.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={submit} className="clean-card p-5 sm:p-6 rounded-3xl space-y-4">
      <h3 className="text-xs font-bold uppercase tracking-wider text-[#15803D] flex items-center gap-2">
        <CalendarClock size={15} /> Phun hôm nay, bao giờ được hái?
      </h3>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <label htmlFor="phi-date" className="block text-[11px] font-bold text-slate-600 mb-1">Ngày phun</label>
          <input id="phi-date" type="date" value={appliedOn} onChange={(e) => setAppliedOn(e.target.value)} className="input-clean py-2 text-sm" />
        </div>
        <div>
          <label htmlFor="phi-days" className="block text-[11px] font-bold text-slate-600 mb-1">Thời gian cách ly (ngày)</label>
          <input id="phi-days" inputMode="numeric" placeholder="xem trên nhãn" value={phi} onChange={(e) => setPhi(e.target.value)} className="input-clean py-2 text-sm" />
        </div>
      </div>
      <button type="submit" disabled={loading} className="btn-primary text-xs py-2.5 px-5">
        {loading ? <Loader2 size={15} className="animate-spin" /> : <CalendarClock size={15} />}
        <span>Tính ngày thu hoạch</span>
      </button>
      {result?.harvest_safe_on && (
        <div className="p-4 rounded-2xl bg-[#F0FDF4] border border-emerald-200 text-sm" aria-live="polite">
          Được thu hoạch từ ngày <b className="text-[#14532D]">{formatDate(result.harvest_safe_on)}</b>
          {result.days_remaining ? ` (còn ${result.days_remaining} ngày).` : ' — đã qua thời gian cách ly.'}
          <p className="text-[11px] text-slate-500 mt-1.5">
            Nếu phun nhiều loại thuốc, lấy ngày muộn nhất. Hàng xuất khẩu (đặc biệt sầu riêng) cần tuân thủ thêm quy định dư lượng của nước nhập khẩu.
          </p>
        </div>
      )}
    </form>
  );
}

export function ToolsPage() {
  return (
    <div className="space-y-8">
      <div className="space-y-1.5">
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[#0F172A] tracking-tight font-['Space_Grotesk']">
          Công Cụ <span className="text-gradient">Phun Thuốc</span>
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 max-w-2xl">
          Tính lượng thuốc cần pha theo diện tích và bình phun, ước tính chi phí, và ngày được thu hoạch sau khi phun.
        </p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-7"><DoseCalculator /></div>
        <div className="lg:col-span-5"><HarvestCalculator /></div>
      </div>
    </div>
  );
}

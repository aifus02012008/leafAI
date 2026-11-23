import { useState, type FormEvent } from 'react';
import { Calculator, Loader2 } from 'lucide-react';
import { apiCalcDose } from '../api/treatments';
import { showToast } from './Toast';
import { AREA_UNIT_LABELS, formatNumber, formatVnd } from '../utils/format';
import type { AreaUnit, DoseBasis, DoseRequest, DoseResult } from '../types';

interface DoseCalculatorProps {
  onComputed?: (request: DoseRequest, result: DoseResult) => void;
  /** Called when any input changes, so callers can drop a now-stale result. */
  onChange?: () => void;
  compact?: boolean;
}

const TANK_SIZES = [8, 16, 20, 25];

/** Parse Vietnamese-formatted numbers: "150.000" -> 150000, "1.500,5" -> 1500.5, "0,5" -> 0.5. */
function toNumber(value: string): number | null {
  let s = value.trim().replace(/\s/g, '');
  if (!s) return null;
  if (s.includes(',')) {
    s = s.replace(/\./g, '').replace(',', '.');
  } else if (/^\d{1,3}(\.\d{3})+$/.test(s)) {
    s = s.replace(/\./g, '');
  }
  const n = Number(s);
  return Number.isFinite(n) && n > 0 ? n : null;
}

/** Spray mixing calculator. The label dose is always typed from the product label. */
export function DoseCalculator({ onComputed, onChange, compact = false }: DoseCalculatorProps) {
  const [area, setArea] = useState('1');
  const [areaUnit, setAreaUnit] = useState<AreaUnit>('sao_bac_bo');
  const [tank, setTank] = useState('16');
  const [labelDose, setLabelDose] = useState('');
  const [basis, setBasis] = useState<DoseBasis>('per_tank');
  const [labelTank, setLabelTank] = useState('16');
  const [water, setWater] = useState('500');
  const [packSize, setPackSize] = useState('');
  const [packPrice, setPackPrice] = useState('');
  const [result, setResult] = useState<DoseResult | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const req: DoseRequest = {
      area: toNumber(area) ?? 0,
      area_unit: areaUnit,
      tank_l: toNumber(tank) ?? 0,
      label_dose: toNumber(labelDose) ?? 0,
      label_dose_basis: basis,
      label_tank_l: basis === 'per_tank' ? toNumber(labelTank) : null,
      water_l_per_ha: toNumber(water) ?? 0,
      pack_size: toNumber(packSize),
      pack_price: toNumber(packPrice),
    };
    if (!req.area || !req.tank_l || !req.label_dose || !req.water_l_per_ha) {
      showToast('error', 'Vui lòng nhập đủ diện tích, dung tích bình, liều trên nhãn và lượng nước.');
      return;
    }
    if ((req.pack_size === null) !== (req.pack_price === null)) {
      showToast('error', 'Nhập cả quy cách chai/gói và giá để ước tính chi phí.');
      return;
    }
    setLoading(true);
    try {
      const res = await apiCalcDose(req);
      setResult(res);
      onComputed?.(req, res);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      showToast('error', typeof detail === 'string' ? detail : 'Không tính được. Kiểm tra lại số liệu.');
    } finally {
      setLoading(false);
    }
  };

  const label = 'block text-[11px] font-bold text-slate-600 mb-1';
  return (
    <form
      onSubmit={submit}
      onChange={() => {
        setResult(null);
        onChange?.();
      }}
      className={`space-y-4 ${compact ? '' : 'clean-card p-5 sm:p-6 rounded-3xl'}`}>
      {!compact && (
        <h3 className="text-xs font-bold uppercase tracking-wider text-[#1F7A4D] flex items-center gap-2">
          <Calculator size={15} /> Tính liều pha thuốc
        </h3>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label className={label} htmlFor="dose-area">Diện tích cần phun</label>
          <div className="flex gap-2">
            {/* input-clean is width:100%, so size via wrappers */}
            <div className="w-20 shrink-0">
              <input id="dose-area" inputMode="decimal" value={area} onChange={(e) => setArea(e.target.value)} className="input-clean py-2 text-sm" />
            </div>
            <div className="flex-1 min-w-0">
            <select aria-label="Đơn vị diện tích" value={areaUnit} onChange={(e) => setAreaUnit(e.target.value as AreaUnit)} className="input-clean py-2 text-sm">
              {(Object.keys(AREA_UNIT_LABELS) as AreaUnit[]).map((u) => (
                <option key={u} value={u}>{AREA_UNIT_LABELS[u]}</option>
              ))}
            </select>
            </div>
          </div>
        </div>
        <div>
          <label className={label} htmlFor="dose-tank">Bình phun (lít)</label>
          <select id="dose-tank" value={tank} onChange={(e) => setTank(e.target.value)} className="input-clean py-2 text-sm">
            {TANK_SIZES.map((t) => <option key={t} value={t}>Bình {t} lít</option>)}
          </select>
        </div>
      </div>

      <div className="p-3.5 rounded-2xl bg-amber-50/70 border border-amber-200 space-y-3">
        <p className="text-[11px] font-bold text-amber-900">Trên nhãn</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className={label} htmlFor="dose-label">Liều (ml/g)</label>
            <input id="dose-label" inputMode="decimal" placeholder="vd: 20" value={labelDose} onChange={(e) => setLabelDose(e.target.value)} className="input-clean py-2 text-sm" />
          </div>
          <div>
            <span className={label}>Liều tính theo</span>
            <div className="flex gap-1.5" role="radiogroup" aria-label="Liều tính theo">
              {([['per_tank', 'mỗi bình'], ['per_ha', 'mỗi ha']] as [DoseBasis, string][]).map(([v, l]) => (
                <button key={v} type="button" role="radio" aria-checked={basis === v} onClick={() => setBasis(v)}
                  className={`flex-1 py-2 rounded-xl text-xs font-bold border ${basis === v ? 'bg-[#1F7A4D] text-white border-[#1F7A4D]' : 'bg-white text-slate-700 border-slate-200'}`}>
                  {l}
                </button>
              ))}
            </div>
          </div>
          {basis === 'per_tank' && (
            <div>
              <label className={label} htmlFor="dose-label-tank">Nhãn ghi cho bình (lít)</label>
              <input id="dose-label-tank" inputMode="decimal" value={labelTank} onChange={(e) => setLabelTank(e.target.value)} className="input-clean py-2 text-sm" />
            </div>
          )}
          <div>
            <label className={label} htmlFor="dose-water">Nước (lít/ha)</label>
            <input id="dose-water" inputMode="decimal" value={water} onChange={(e) => setWater(e.target.value)} className="input-clean py-2 text-sm" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className={label} htmlFor="dose-pack">Chai/gói (ml/g)</label>
          <input id="dose-pack" inputMode="decimal" placeholder="vd: 100" value={packSize} onChange={(e) => setPackSize(e.target.value)} className="input-clean py-2 text-sm" />
        </div>
        <div>
          <label className={label} htmlFor="dose-price">Giá mỗi chai/gói (đ)</label>
          <input id="dose-price" inputMode="numeric" placeholder="vd: 45000" value={packPrice} onChange={(e) => setPackPrice(e.target.value)} className="input-clean py-2 text-sm" />
        </div>
      </div>

      <button type="submit" disabled={loading} className="btn-primary text-xs py-2.5 px-5 w-full sm:w-auto">
        {loading ? <Loader2 size={15} className="animate-spin" /> : <Calculator size={15} />}
        <span>Tính liều</span>
      </button>

      {result && (
        <div className="grid grid-cols-2 gap-2.5 text-xs" aria-live="polite">
          <Stat label="Mỗi bình pha" value={`${formatNumber(result.product_per_tank)} ml/g`} highlight />
          <Stat label="Số bình cần phun" value={`${result.tanks_needed} bình`} highlight />
          <Stat label="Tổng lượng thuốc" value={`${formatNumber(result.total_product)} ml/g`} />
          <Stat label="Tổng lượng nước" value={`${formatNumber(result.total_water_l)} lít`} />
          {result.estimated_cost !== null && (
            <Stat label={`Chi phí ước tính (${result.packs_needed} chai/gói)`} value={formatVnd(result.estimated_cost)} />
          )}
          <p className="col-span-2 text-[10px] text-slate-500">
            Kết quả chỉ là phép tính từ số liệu bạn nhập. Luôn kiểm tra lại với nhãn thuốc và mặc đồ bảo hộ khi phun.
          </p>
        </div>
      )}
    </form>
  );
}

function Stat({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={`p-3 rounded-xl border ${highlight ? 'bg-[#EAF5EE] border-emerald-200' : 'bg-white border-[#DCE5DC]'}`}>
      <span className="block text-[10px] text-slate-500 font-semibold">{label}</span>
      <span className="block text-sm font-extrabold text-slate-900 font-mono">{value}</span>
    </div>
  );
}

import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, SprayCan, X } from 'lucide-react';
import { apiCreateTreatment, apiGetActives } from '../api/treatments';
import { DoseCalculator } from './DoseCalculator';
import { showToast } from './Toast';
import { todayIso } from '../utils/format';
import type { ActiveIngredient, CropCode, DoseResult } from '../types';

interface RecordTreatmentModalProps {
  open: boolean;
  diagnosisId: number;
  cropCode: CropCode;
  diseaseName: string | null;
  onClose: () => void;
}

/** "Ghi nhận đã phun thuốc": logs the spray, schedules a re-photo, and tracks the harvest wait. */
export function RecordTreatmentModal({ open, diagnosisId, cropCode, diseaseName, onClose }: RecordTreatmentModalProps) {
  const navigate = useNavigate();
  const [actives, setActives] = useState<ActiveIngredient[]>([]);
  const [activeCode, setActiveCode] = useState('');
  const [productName, setProductName] = useState('');
  const [appliedOn, setAppliedOn] = useState(todayIso());
  const [phiDays, setPhiDays] = useState('');
  const [followupDays, setFollowupDays] = useState(4);
  const [showCalc, setShowCalc] = useState(false);
  const [dose, setDose] = useState<{ area_m2: number; result: DoseResult } | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!open) return;
    let active = true;
    apiGetActives(cropCode, diseaseName)
      .then((list) => {
        if (!active) return;
        setActives(list);
        const firstRecommended = list.find((a) => a.recommended && !a.banned);
        setActiveCode(firstRecommended?.code ?? '');
      })
      .catch(() => showToast('error', 'Không tải được danh mục hoạt chất.'));
    return () => {
      active = false;
    };
  }, [open, cropCode, diseaseName]);

  if (!open) return null;

  const recommended = actives.filter((a) => a.recommended);
  const others = actives.filter((a) => !a.recommended);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!activeCode) {
      showToast('error', 'Vui lòng chọn hoạt chất đã phun.');
      return;
    }
    if (!appliedOn) {
      showToast('error', 'Vui lòng chọn ngày phun.');
      return;
    }
    const phi = phiDays.trim() === '' ? null : Number(phiDays);
    if (phi !== null && (!Number.isInteger(phi) || phi < 0 || phi > 365)) {
      showToast('error', 'Thời gian cách ly phải là số ngày (0–365).');
      return;
    }
    setSaving(true);
    try {
      await apiCreateTreatment({
        diagnosis_id: diagnosisId,
        active_code: activeCode,
        product_name: productName.trim() || null,
        disease_name: diseaseName,
        applied_on: appliedOn,
        phi_days: phi,
        followup_days: followupDays,
        area_m2: dose?.area_m2 ?? null,
        total_product: dose?.result.total_product ?? null,
        estimated_cost: dose?.result.estimated_cost ?? null,
      });
      showToast('success', `Đã lưu. LEAF AI sẽ nhắc bạn chụp lại lá sau ${followupDays} ngày.`);
      onClose();
      navigate('/treatments');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      showToast('error', typeof detail === 'string' ? detail : 'Không lưu được lần điều trị.');
    } finally {
      setSaving(false);
    }
  };

  const optionLabel = (a: ActiveIngredient) =>
    `${a.name}${a.moa_code ? ` · nhóm ${a.moa_scheme} ${a.moa_code}` : ''}${a.banned ? ' · ĐÃ BỊ CẤM' : ''}`;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-slate-900/60" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="record-treatment-title"
        className="w-full sm:max-w-2xl max-h-[92vh] overflow-y-auto bg-white rounded-t-3xl sm:rounded-3xl shadow-2xl p-5 sm:p-7 space-y-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 id="record-treatment-title" className="text-lg font-extrabold text-slate-900 flex items-center gap-2 font-display">
              <SprayCan size={18} className="text-[#1F7A4D]" /> Ghi nhận đã phun thuốc
            </h2>
            {diseaseName && <p className="text-xs text-slate-500 mt-0.5">Bệnh: {diseaseName}</p>}
          </div>
          <button type="button" onClick={onClose} aria-label="Đóng" className="p-2 rounded-full hover:bg-slate-100">
            <X size={16} />
          </button>
        </div>

        <form id="record-treatment-form" onSubmit={submit} className="space-y-4 text-sm">
          <div>
            <label htmlFor="tr-active" className="block text-[11px] font-bold text-slate-600 mb-1">Hoạt chất đã phun</label>
            <select id="tr-active" value={activeCode} onChange={(e) => setActiveCode(e.target.value)} className="input-clean py-2 text-sm">
              <option value="">— Hoạt chất —</option>
              {recommended.length > 0 && (
                <optgroup label="Gợi ý cho bệnh này">
                  {recommended.map((a) => <option key={a.code} value={a.code}>{optionLabel(a)}</option>)}
                </optgroup>
              )}
              <optgroup label="Hoạt chất khác">
                {others.map((a) => <option key={a.code} value={a.code} disabled={a.banned}>{optionLabel(a)}</option>)}
              </optgroup>
            </select>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label htmlFor="tr-product" className="block text-[11px] font-bold text-slate-600 mb-1">Tên thuốc</label>
              <input id="tr-product" maxLength={200} value={productName} onChange={(e) => setProductName(e.target.value)} className="input-clean py-2 text-sm" />
            </div>
            <div>
              <label htmlFor="tr-date" className="block text-[11px] font-bold text-slate-600 mb-1">Ngày phun</label>
              <input id="tr-date" type="date" max={todayIso()} value={appliedOn} onChange={(e) => setAppliedOn(e.target.value)} className="input-clean py-2 text-sm" />
            </div>
            <div>
              <label htmlFor="tr-phi" className="block text-[11px] font-bold text-slate-600 mb-1">Cách ly (ngày)</label>
              <input id="tr-phi" inputMode="numeric" placeholder="vd: 7" value={phiDays} onChange={(e) => setPhiDays(e.target.value)} className="input-clean py-2 text-sm" />
            </div>
            <div>
              <label htmlFor="tr-followup" className="block text-[11px] font-bold text-slate-600 mb-1">Nhắc chụp lại lá sau</label>
              <select id="tr-followup" value={followupDays} onChange={(e) => setFollowupDays(Number(e.target.value))} className="input-clean py-2 text-sm">
                {[3, 4, 5, 6, 7].map((d) => <option key={d} value={d}>{d} ngày</option>)}
              </select>
            </div>
          </div>
        </form>

        {/* Calculator has its own <form>; kept outside to avoid nested forms. */}
        <div className="rounded-2xl border border-[#DCE5DC] p-3.5 text-sm">
            <button type="button" onClick={() => setShowCalc((v) => !v)} className="text-xs font-bold text-[#1F7A4D]">
              {showCalc ? '− Ẩn máy tính liều' : '+ Tính liều pha & chi phí (tùy chọn)'}
            </button>
            {showCalc && (
              <div className="mt-3">
                <DoseCalculator compact onComputed={(_req, result) => setDose({ area_m2: result.area_m2, result })} onChange={() => setDose(null)} />
              </div>
            )}
        </div>

        <div className="flex justify-end gap-2.5">
            <button type="button" onClick={onClose} className="btn-secondary text-xs py-2 px-4">Hủy</button>
            <button type="submit" form="record-treatment-form" disabled={saving} className="btn-primary text-xs py-2.5 px-5">
              {saving ? <Loader2 size={15} className="animate-spin" /> : <SprayCan size={15} />}
              <span>Lưu lần phun</span>
            </button>
        </div>
      </div>
    </div>
  );
}

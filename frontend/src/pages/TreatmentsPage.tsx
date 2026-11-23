import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Camera, CalendarClock, ClipboardList, SprayCan, Trash2 } from 'lucide-react';
import { apiDeleteTreatment, apiListTreatments } from '../api/treatments';
import { resolveMediaUrl } from '../api/client';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { EmptyState } from '../components/EmptyState';
import { LoadingState } from '../components/LoadingState';
import { showToast } from '../components/Toast';
import { useCrops } from '../hooks/useCrops';
import { VERDICT_META, daysUntil, formatDate, formatNumber } from '../utils/format';
import type { Treatment } from '../types';

function HarvestBadge({ treatment }: { treatment: Treatment }) {
  if (!treatment.harvest_safe_on) {
    return <span className="text-[11px] text-slate-500">Chưa nhập thời gian cách ly</span>;
  }
  const days = daysUntil(treatment.harvest_safe_on);
  if (days <= 0) {
    return (
      <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200">
        Đã qua thời gian cách ly
      </span>
    );
  }
  return (
    <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-red-50 text-red-700 border border-red-200">
      Chưa được thu hoạch · còn {days} ngày (từ {formatDate(treatment.harvest_safe_on)})
    </span>
  );
}

export function TreatmentsPage() {
  const navigate = useNavigate();
  const { cropName } = useCrops();
  const [items, setItems] = useState<Treatment[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    let active = true;
    apiListTreatments()
      .then((data) => active && setItems(data))
      .catch(() => showToast('error', 'Không tải được nhật ký điều trị.'))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  const due = items.filter((t) => t.status === 'awaiting_followup' && daysUntil(t.followup_due_on) <= 0);
  const waitingHarvest = items.filter((t) => t.harvest_safe_on && daysUntil(t.harvest_safe_on) > 0);

  const startFollowup = (t: Treatment) => navigate(`/diagnose?followup=${t.id}&crop=${encodeURIComponent(t.crop_code)}`);

  const confirmDelete = async () => {
    if (deleteId === null) return;
    setDeleting(true);
    try {
      await apiDeleteTreatment(deleteId);
      setItems((prev) => prev.filter((t) => t.id !== deleteId));
      setDeleteId(null);
    } catch {
      showToast('error', 'Xóa thất bại.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-8">
      <div className="space-y-1.5">
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[#0F172A] tracking-tight font-['Space_Grotesk']">
          Nhật Ký <span className="text-gradient">Điều Trị</span>
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 max-w-2xl">
          Theo dõi các lần phun thuốc, ngày được thu hoạch và đánh giá thuốc có tác dụng hay không bằng ảnh chụp lại.
        </p>
      </div>

      {(due.length > 0 || waitingHarvest.length > 0) && (
        <section aria-labelledby="todo-title" className="clean-card p-5 rounded-3xl space-y-3">
          <h2 id="todo-title" className="text-xs font-bold uppercase tracking-wider text-[#15803D] flex items-center gap-2">
            <ClipboardList size={15} /> Việc cần làm
          </h2>
          <ul className="space-y-2 text-sm">
            {due.map((t) => (
              <li key={`due-${t.id}`} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-2xl bg-amber-50/70 border border-amber-200">
                <span>
                  <b>Chụp lại lá {cropName(t.crop_code).toLowerCase()}</b> để kiểm tra hiệu quả {t.active_name} (phun {formatDate(t.applied_on)})
                </span>
                <button type="button" onClick={() => startFollowup(t)} className="btn-primary text-xs py-2 px-3.5 shrink-0">
                  <Camera size={14} /> <span>Chụp lại ngay</span>
                </button>
              </li>
            ))}
            {waitingHarvest.map((t) => (
              <li key={`phi-${t.id}`} className="flex items-center gap-2 p-3 rounded-2xl bg-red-50/60 border border-red-200">
                <CalendarClock size={15} className="text-red-600 shrink-0" />
                <span>
                  Vườn {cropName(t.crop_code).toLowerCase()}: <b>không thu hoạch trước {formatDate(t.harvest_safe_on)}</b> (cách ly {t.active_name})
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {loading ? (
        <LoadingState message="Đang tải nhật ký điều trị..." />
      ) : items.length === 0 ? (
        <EmptyState
          icon={<SprayCan size={24} className="text-[#15803D]" />}
          title="Chưa có lần điều trị nào"
          description='Sau khi chẩn đoán phát hiện bệnh, bấm "Ghi nhận đã phun thuốc" để LEAF AI nhắc chụp lại lá và đánh giá hiệu quả.'
          action={<button type="button" onClick={() => navigate('/diagnose')} className="btn-primary text-xs">Đi tới chẩn đoán</button>}
        />
      ) : (
        <ul className="space-y-4">
          {items.map((t) => {
            const latest = t.followups[t.followups.length - 1];
            const followupDays = daysUntil(t.followup_due_on);
            return (
              <li key={t.id} className="clean-card p-4 sm:p-5 rounded-3xl flex flex-col sm:flex-row gap-4">
                {t.original_image_url && (
                  <img src={resolveMediaUrl(t.original_image_url)} alt="Ảnh lá trước điều trị" className="w-20 h-20 rounded-2xl object-cover border border-[#E2EFE7] shrink-0" />
                )}
                <div className="flex-1 min-w-0 space-y-1.5 text-xs">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-bold text-[#14532D] px-2 py-0.5 rounded-md bg-emerald-50 border border-emerald-200">{cropName(t.crop_code)}</span>
                    <h3 className="text-sm font-bold text-slate-900 truncate">{t.disease_name || 'Chưa rõ bệnh'}</h3>
                  </div>
                  <p className="text-slate-600">
                    Phun <b>{t.active_name}</b>{t.moa_code ? ` (nhóm ${t.moa_code})` : ''}{t.product_name ? ` — ${t.product_name}` : ''} ngày {formatDate(t.applied_on)}
                    {t.severity_before !== null && ` · vết bệnh ban đầu ${formatNumber(t.severity_before)}%`}
                  </p>
                  <div className="flex flex-wrap gap-2 items-center">
                    <HarvestBadge treatment={t} />
                    {latest ? (
                      <span className={`text-[11px] font-bold px-2 py-0.5 rounded-md border ${VERDICT_META[latest.verdict].className}`}>
                        {VERDICT_META[latest.verdict].label}
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-500">
                        {followupDays > 0 ? `Chụp lại sau ${followupDays} ngày (${formatDate(t.followup_due_on)})` : 'Đã đến hạn chụp lại lá'}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex sm:flex-col gap-2 shrink-0">
                  <button type="button" onClick={() => startFollowup(t)} className="btn-secondary text-xs py-2 px-3">
                    <Camera size={14} /> <span>{latest ? 'Chụp lại lần nữa' : 'Chụp lại lá'}</span>
                  </button>
                  <button type="button" onClick={() => setDeleteId(t.id)} aria-label="Xóa lần điều trị" className="p-2 rounded-xl border border-red-200 text-red-600 hover:bg-red-50 self-end">
                    <Trash2 size={14} />
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}

      <ConfirmDialog
        open={deleteId !== null}
        title="Xóa lần điều trị?"
        message="Lần phun và các kết quả tái khám liên quan sẽ bị xóa khỏi nhật ký."
        loading={deleting}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  );
}

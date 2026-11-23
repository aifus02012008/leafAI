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
    return <span className="text-[11px] text-slate-500">Chưa có cách ly</span>;
  }
  const days = daysUntil(treatment.harvest_safe_on);
  if (days <= 0) {
    return (
      <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200">
        Hết cách ly
      </span>
    );
  }
  return (
    <span className="text-[11px] font-bold px-2 py-0.5 rounded-md bg-red-50 text-red-700 border border-red-200">
      Cách ly · còn {days} ngày
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
    <div className="space-y-6">

      {(due.length > 0 || waitingHarvest.length > 0) && (
        <section aria-labelledby="todo-title" className="clean-card p-5 space-y-3">
          <h2 id="todo-title" className="text-xs font-bold uppercase tracking-wider text-[#1F7A4D] flex items-center gap-2">
            <ClipboardList size={15} /> Việc cần làm
          </h2>
          <ul className="grid grid-cols-1 xl:grid-cols-2 gap-2 text-sm">
            {due.map((t) => (
              <li key={`due-${t.id}`} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-2xl bg-amber-50/70 border border-amber-200">
                <span>
                  <b>{cropName(t.crop_code)}</b> · {t.active_name} · {formatDate(t.applied_on)}
                </span>
                <button type="button" onClick={() => startFollowup(t)} className="btn-primary text-xs py-2 px-3.5 shrink-0">
                  <Camera size={14} /> <span>Chụp lại</span>
                </button>
              </li>
            ))}
            {waitingHarvest.map((t) => (
              <li key={`phi-${t.id}`} className="flex items-center gap-2 p-3 rounded-2xl bg-red-50/60 border border-red-200">
                <CalendarClock size={15} className="text-red-600 shrink-0" />
                <span>
                  {cropName(t.crop_code)}: <b>thu hoạch từ {formatDate(t.harvest_safe_on)}</b>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {loading ? (
        <LoadingState message="Đang tải…" />
      ) : items.length === 0 ? (
        <EmptyState
          icon={<SprayCan size={24} className="text-[#1F7A4D]" />}
          title="Chưa có lần phun"
          action={<button type="button" onClick={() => navigate('/diagnose')} className="btn-primary text-xs">Chụp lá</button>}
        />
      ) : (
        <ul className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {items.map((t) => {
            const latest = t.followups[t.followups.length - 1];
            const followupDays = daysUntil(t.followup_due_on);
            return (
              <li key={t.id} className="clean-card p-4 flex flex-col sm:flex-row gap-4">
                {t.original_image_url && (
                  <img src={resolveMediaUrl(t.original_image_url)} alt="Ảnh lá trước điều trị" className="w-20 h-20 rounded-2xl object-cover border border-[#DCE5DC] shrink-0" />
                )}
                <div className="flex-1 min-w-0 space-y-1.5 text-xs">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-bold text-[#0F2A20] px-2 py-0.5 rounded-md bg-emerald-50 border border-emerald-200">{cropName(t.crop_code)}</span>
                    <h3 className="text-sm font-bold text-slate-900 truncate">{t.disease_name || 'Chưa rõ bệnh'}</h3>
                  </div>
                  <p className="text-slate-600">
                    <b>{t.active_name}</b> · {formatDate(t.applied_on)}
                    {t.severity_before !== null && ` · ${formatNumber(t.severity_before)}%`}
                  </p>
                  <div className="flex flex-wrap gap-2 items-center">
                    <HarvestBadge treatment={t} />
                    {latest ? (
                      <span className={`text-[11px] font-bold px-2 py-0.5 rounded-md border ${VERDICT_META[latest.verdict].className}`}>
                        {VERDICT_META[latest.verdict].label}
                      </span>
                    ) : (
                      <span className="text-[11px] text-slate-500">
                        {followupDays > 0 ? `Chụp lại sau ${followupDays} ngày` : 'Đến hạn chụp lại'}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex sm:flex-col gap-2 shrink-0">
                  <button type="button" onClick={() => startFollowup(t)} className="btn-secondary text-xs py-2 px-3">
                    <Camera size={14} /> <span>Chụp lại</span>
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
        message="Không khôi phục được."
        loading={deleting}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteId(null)}
      />
    </div>
  );
}

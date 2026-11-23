import { useState } from 'react';
import { HelpCircle, Loader2, ThumbsDown, ThumbsUp } from 'lucide-react';
import { apiSubmitFeedback } from '../api/diagnosis';
import { showToast } from './Toast';
import type { FeedbackValue } from '../types';

interface DiagnosisFeedbackProps {
  diagnosisId: number;
  initial?: FeedbackValue | null;
}

const OPTIONS: { value: FeedbackValue; label: string; icon: typeof ThumbsUp }[] = [
  { value: 'correct', label: 'Đúng', icon: ThumbsUp },
  { value: 'incorrect', label: 'Sai', icon: ThumbsDown },
  { value: 'unsure', label: 'Không chắc', icon: HelpCircle },
];

/** Asks the grower to confirm the result — the answers feed model retraining. */
export function DiagnosisFeedback({ diagnosisId, initial = null }: DiagnosisFeedbackProps) {
  const [selected, setSelected] = useState<FeedbackValue | null>(initial);
  const [pending, setPending] = useState<FeedbackValue | null>(null);

  const submit = async (value: FeedbackValue) => {
    if (pending) return;
    setPending(value);
    try {
      const res = await apiSubmitFeedback(diagnosisId, value);
      setSelected(res.user_feedback);
      showToast('success', 'Cảm ơn bạn! Phản hồi giúp LEAF AI chẩn đoán chính xác hơn.');
    } catch (err: any) {
      showToast('error', err.response?.data?.detail || 'Không gửi được phản hồi. Vui lòng thử lại.');
    } finally {
      setPending(null);
    }
  };

  return (
    <div className="p-4 rounded-2xl bg-white/60 border border-[#E2EFE7] space-y-2.5">
      <span className="block font-bold text-slate-900 text-xs">Kết quả này có đúng không?</span>
      <div className="flex flex-wrap gap-2">
        {OPTIONS.map(({ value, label, icon: Icon }) => {
          const active = selected === value;
          return (
            <button
              key={value}
              type="button"
              aria-pressed={active}
              disabled={pending !== null}
              onClick={() => submit(value)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold border transition-all cursor-pointer disabled:cursor-wait ${
                active
                  ? 'bg-[#15803D] text-white border-[#15803D]'
                  : 'bg-white text-slate-700 border-slate-200 hover:border-emerald-300'
              }`}
            >
              {pending === value ? <Loader2 size={13} className="animate-spin" /> : <Icon size={13} />}
              {label}
            </button>
          );
        })}
      </div>
      {selected && (
        <p className="text-[11px] text-slate-500">Đã ghi nhận phản hồi. Bạn có thể đổi lựa chọn bất cứ lúc nào.</p>
      )}
    </div>
  );
}

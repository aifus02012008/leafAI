import { Link } from 'react-router-dom';
import { BookOpen, CheckCircle2, Droplets, MessageCircle, Sparkles, SprayCan, Scissors } from 'lucide-react';
import { openChat } from '../assistant/chatEvents';
import { DiagnosisFeedback } from '../DiagnosisFeedback';
import { formatNumber } from '../../utils/format';
import type { Detection, DiagnosisResult } from '../../types';
import type { ReactNode } from 'react';

interface DiagnosisVerdictProps {
  result: DiagnosisResult;
  canRecordTreatment: boolean;
  onRecordTreatment: () => void;
  followupSlot?: ReactNode;
}

function topDetection(detections: readonly Detection[]): Detection | null {
  return detections.reduce<Detection | null>((best, d) => (!best || d.confidence > best.confidence ? d : best), null);
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-white border border-line px-3 py-2.5">
      <p className="text-[11px] text-ink/55">{label}</p>
      <p className="font-mono text-sm font-semibold text-ink mt-0.5">{value}</p>
    </div>
  );
}

const NEXT_STEPS = [
  { icon: Scissors, label: 'Cắt bỏ lá bệnh' },
  { icon: Droplets, label: 'Tỉa tán, thoát nước' },
] as const;

/** The answer to "what's wrong with my leaf?", then what to do about it. */
export function DiagnosisVerdict({ result, canRecordTreatment, onRecordTreatment, followupSlot }: DiagnosisVerdictProps) {
  const top = topDetection(result.detections);
  const confidencePct = top ? Math.round(top.confidence * 100) : null;
  const byGemini = result.analysis_source === 'gemini';
  const askDoctor = () =>
    openChat({
      diagnosisId: result.id,
      label: top ? `${top.class_name.split(' (')[0]} · ${confidencePct}%` : 'Lá khoẻ',
    });

  return (
    <div className="space-y-4">
      {byGemini && (
        <p
          className="inline-flex items-center gap-1.5 rounded-full bg-sun-wash text-[#8A6A00] px-3 py-1 text-xs font-bold"
          title="Kết quả do Gemini AI phân tích, chỉ để tham khảo"
        >
          <Sparkles size={13} /> AI tham khảo
        </p>
      )}
      {top ? (
        <div className="rounded-[18px] p-6 space-y-4 bg-forest text-white">
          <h2 className="font-display text-2xl font-extrabold leading-tight">{top.class_name}</h2>
          <div className="space-y-1.5">
            <div className="flex items-baseline justify-between text-sm">
              <span className="text-white/70">Độ tin cậy</span>
              <span className="font-mono font-semibold text-mint">{confidencePct}%</span>
            </div>
            <div className="h-2 rounded-full bg-white/15 overflow-hidden" role="presentation">
              <div className="h-full rounded-full bg-mint" style={{ width: `${confidencePct}%` }} />
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-[18px] p-6 bg-leaf-wash flex items-center gap-3">
          <CheckCircle2 size={28} className="text-leaf shrink-0" />
          <h2 className="font-display text-2xl font-extrabold text-ink">Lá khoẻ</h2>
        </div>
      )}

      <div className="grid grid-cols-3 gap-2">
        <Stat label="Vùng bệnh" value={String(result.detections.length)} />
        <Stat label="Diện tích" value={result.severity_pct != null ? `${formatNumber(result.severity_pct)}%` : '—'} />
        <Stat label="Thời gian" value={result.inference_time != null ? `${result.inference_time.toFixed(1)} s` : '—'} />
      </div>

      {followupSlot}

      <button type="button" onClick={askDoctor} className="btn-secondary w-full text-sm py-2.5">
        <MessageCircle size={16} className="text-leaf" />
        Hỏi bác sĩ AI
      </button>

      {top && (
        <div className="clean-card p-4 space-y-3">
          <ul className="grid grid-cols-2 gap-2 text-sm font-medium text-ink">
            {NEXT_STEPS.map(({ icon: Icon, label }) => (
              <li key={label} className="flex items-center gap-2 rounded-xl bg-paper px-3 py-2.5">
                <Icon size={16} className="text-leaf shrink-0" />
                {label}
              </li>
            ))}
          </ul>
          <div className="flex gap-2">
            <Link to="/diseases" className="btn-secondary flex-1 text-sm py-2.5">
              <BookOpen size={16} />
              Phác đồ
            </Link>
            {canRecordTreatment && (
              <button
                type="button"
                onClick={onRecordTreatment}
                className="btn-primary flex-1 text-sm py-2.5"
                title="Nhắc chụp lại sau 3–5 ngày"
              >
                <SprayCan size={16} />
                Ghi lần phun
              </button>
            )}
          </div>
        </div>
      )}

      <DiagnosisFeedback key={result.id} diagnosisId={result.id} initial={result.user_feedback} />
    </div>
  );
}

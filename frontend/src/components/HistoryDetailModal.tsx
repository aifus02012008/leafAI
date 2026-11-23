import { useEffect } from 'react';
import { X, Calendar, Clock, Crosshair, Trash2 } from 'lucide-react';
import { BoundingBoxViewer } from './BoundingBoxViewer';
import type { DiagnosisResult } from '../types';

interface HistoryDetailModalProps {
  diagnosis: DiagnosisResult | null;
  onClose: () => void;
  onDeleteRequest: (id: number) => void;
}

export function HistoryDetailModal({ diagnosis, onClose, onDeleteRequest }: HistoryDetailModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!diagnosis) return null;

  const formattedDate = new Date(diagnosis.created_at).toLocaleString();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150 font-sans"
      onClick={onClose}
    >
      <div
        className="w-full max-w-4xl lg:max-w-5xl max-h-[92vh] overflow-y-auto bg-white rounded-3xl shadow-2xl border border-[#DCE5DC] relative flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-20 flex items-center justify-between px-6 py-5 sm:px-8 sm:py-6 bg-white/95 backdrop-blur-md border-b border-[#DCE5DC]">
          <div>
            <div className="flex items-center gap-2">
              <span
                className={`text-[10px] uppercase font-mono tracking-wider px-2.5 py-0.5 rounded-full font-bold ${
                  diagnosis.status === 'detected'
                    ? 'bg-amber-50 text-amber-800 border border-amber-200'
                    : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                }`}
              >
                {diagnosis.status === 'detected' ? 'Đã Nhận Diện Bệnh Hại' : 'Lá Khỏe Mạnh / Không Có Bệnh'}
              </span>
              <span className="text-xs text-slate-500 font-mono font-medium">
                Bản ghi #{diagnosis.id}
              </span>
            </div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-[#10201A] mt-1 font-display">
              Chi Tiết Hồ Sơ Chẩn Đoán
            </h2>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onDeleteRequest(diagnosis.id)}
              className="w-9 h-9 rounded-xl bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 flex items-center justify-center transition-colors cursor-pointer shadow-2xs"
              title="Xóa bản ghi này"
              aria-label="Xóa bản ghi này"
            >
              <Trash2 size={15} />
            </button>
            <button
              type="button"
              onClick={onClose}
              aria-label="Đóng cửa sổ"
              className="w-9 h-9 rounded-xl bg-white hover:bg-slate-100 text-slate-500 hover:text-slate-900 border border-slate-200 flex items-center justify-center transition-colors cursor-pointer shadow-2xs"
            >
              <X size={17} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 sm:p-8 space-y-5">
          {/* Metadata Bar */}
          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-600 p-3.5 rounded-2xl bg-white/60 border border-[#DCE5DC]">
            <div className="flex items-center gap-1.5 font-mono">
              <Calendar size={14} className="text-[#1F7A4D]" />
              <span>{formattedDate}</span>
            </div>
            {diagnosis.inference_time !== null && (
              <div className="flex items-center gap-1.5 font-mono">
                <Clock size={14} className="text-teal-600" />
                <span>độ trễ {(diagnosis.inference_time * 1000).toFixed(0)} ms</span>
              </div>
            )}
            <div className="flex items-center gap-1.5 font-mono">
              <Crosshair size={14} className="text-amber-600" />
              <span>{diagnosis.detections.length} hộp định vị</span>
            </div>
          </div>

          {/* Visual Viewer with Annotations */}
          <BoundingBoxViewer
            originalUrl={diagnosis.original_image_url}
            annotatedUrl={diagnosis.result_image_url}
            detections={diagnosis.detections}
            inferenceTime={diagnosis.inference_time}
            status={diagnosis.status}
          />
        </div>
      </div>
    </div>
  );
}

import { useState } from 'react';
import { Eye, EyeOff, ZoomIn, ZoomOut, RotateCcw, Crosshair } from 'lucide-react';
import { resolveMediaUrl } from '../api/client';
import type { Detection } from '../types';

interface BoundingBoxViewerProps {
  originalUrl: string;
  annotatedUrl?: string | null;
  detections: Detection[];
  inferenceTime?: number | null;
  status: string;
}

export function BoundingBoxViewer({
  originalUrl,
  annotatedUrl,
  detections,
  inferenceTime,
  status,
}: BoundingBoxViewerProps) {
  const [showAnnotations, setShowAnnotations] = useState<boolean>(true);
  const [activeDetectionIndex, setActiveDetectionIndex] = useState<number | null>(null);
  const [zoomLevel, setZoomLevel] = useState<number>(1);

  const hasAnnotated = Boolean(annotatedUrl);
  const currentImageUrl = showAnnotations && hasAnnotated ? annotatedUrl! : originalUrl;

  const handleZoomIn = () => setZoomLevel((z) => Math.min(z + 0.25, 2.5));
  const handleZoomOut = () => setZoomLevel((z) => Math.max(z - 0.25, 0.75));
  const handleResetZoom = () => setZoomLevel(1);

  return (
    <div className="space-y-4">
      {/* Viewer Container */}
      <div className="clean-card rounded-2xl overflow-hidden relative group border border-[#E2EFE7] shadow-sm bg-white">
        {/* Top Floating Controls Bar */}
        <div className="absolute top-4 left-4 right-4 z-20 flex items-center justify-between pointer-events-none gap-2 flex-wrap">
          <div className="pointer-events-auto flex items-center gap-2">
            {hasAnnotated && (
              <button
                type="button"
                onClick={() => setShowAnnotations(!showAnnotations)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold backdrop-blur-md flex items-center gap-1.5 transition-all shadow-sm cursor-pointer ${
                  showAnnotations
                    ? 'bg-[#15803D] text-white shadow-emerald-900/20'
                    : 'bg-white/95 text-slate-700 border border-slate-200 hover:bg-white'
                }`}
              >
                {showAnnotations ? <Eye size={14} /> : <EyeOff size={14} />}
                <span>{showAnnotations ? 'Bật Hộp Định Vị' : 'Xem Ảnh Gốc'}</span>
              </button>
            )}

            <div className="px-3 py-1.5 rounded-xl bg-white/95 backdrop-blur-md border border-slate-200 text-xs font-semibold text-slate-700 flex items-center gap-2 shadow-xs">
              <span
                className={`w-2 h-2 rounded-full ${
                  status === 'detected' ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'
                }`}
              />
              <span>{status === 'detected' ? `Phát hiện ${detections.length} vùng bệnh` : 'Không phát hiện bệnh hại'}</span>
            </div>
          </div>

          <div className="pointer-events-auto flex items-center gap-1 bg-white/95 backdrop-blur-md p-1 rounded-xl border border-slate-200 shadow-xs">
            <button
              type="button"
              onClick={handleZoomIn}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-700 transition-colors cursor-pointer"
              title="Phóng To"
              aria-label="Phóng To"
            >
              <ZoomIn size={14} />
            </button>
            <button
              type="button"
              onClick={handleZoomOut}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-700 transition-colors cursor-pointer"
              title="Thu Nhỏ"
              aria-label="Thu Nhỏ"
            >
              <ZoomOut size={14} />
            </button>
            <button
              type="button"
              onClick={handleResetZoom}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-700 transition-colors cursor-pointer"
              title="Đặt Lại Kích Thước"
              aria-label="Đặt Lại Kích Thước"
            >
              <RotateCcw size={14} />
            </button>
          </div>
        </div>

        {/* Image Display Canvas */}
        <div className="relative min-h-[420px] max-h-[560px] flex items-center justify-center p-6 bg-[#0B1319] overflow-hidden">
          <div
            className="transition-transform duration-200 ease-out flex items-center justify-center w-full h-full"
            style={{ transform: `scale(${zoomLevel})` }}
          >
            <img
              src={resolveMediaUrl(currentImageUrl)}
              alt="Phân tích bệnh học lá cây"
              className="max-h-[500px] w-auto max-w-full object-contain rounded-xl shadow-2xl"
            />
          </div>
        </div>

        {/* Bottom Metadata Ribbon */}
        {inferenceTime !== null && inferenceTime !== undefined && (
          <div className="px-5 py-2.5 bg-[#F8FAF9] border-t border-[#E2EFE7] flex items-center justify-between text-[11px] text-slate-500 font-mono">
            <span>Thời gian suy luận: {(inferenceTime * 1000).toFixed(0)} ms ({inferenceTime.toFixed(3)}s)</span>
            <span className="hidden sm:inline">Độ phân giải thị giác YOLO 640×640 px</span>
          </div>
        )}
      </div>

      {/* Detection Cards Grid */}
      {detections.length > 0 && (
        <div className="space-y-2.5 pt-1">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5 px-1 font-['DM_Sans']">
            <Crosshair size={14} className="text-[#15803D]" />
            Vùng Tổn Thương Được Định Vị ({detections.length})
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {detections.map((det, index) => {
              const cleanName = det.class_name.replace('Tomato___', '').replace(/_/g, ' ');
              const confPct = (det.confidence * 100).toFixed(1);
              const isActive = activeDetectionIndex === index;

              return (
                <div
                  key={det.id || index}
                  onMouseEnter={() => setActiveDetectionIndex(index)}
                  onMouseLeave={() => setActiveDetectionIndex(null)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer ${
                    isActive
                      ? 'bg-[#F0FDF4] border-emerald-400 shadow-sm'
                      : 'bg-white border-[#E2EFE7] hover:border-emerald-300 shadow-2xs'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-extrabold text-[#15803D]">#{index + 1}</span>
                    <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded-md bg-emerald-50 text-[#15803D] border border-emerald-200">
                      {confPct}% Tin cậy
                    </span>
                  </div>

                  <p className="mt-1 text-xs font-bold text-slate-900 truncate font-['DM_Sans']">
                    {cleanName}
                  </p>

                  <div className="mt-1.5 text-[10px] text-slate-400 font-mono flex items-center justify-between">
                    <span>X: {det.x1.toFixed(0)}–{det.x2.toFixed(0)}</span>
                    <span>Y: {det.y1.toFixed(0)}–{det.y2.toFixed(0)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

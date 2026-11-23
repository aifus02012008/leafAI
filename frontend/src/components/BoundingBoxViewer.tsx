import { useState } from 'react';
import { Eye, EyeOff, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';
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
      <div className="clean-card overflow-hidden relative group border border-[#DCE5DC] shadow-sm bg-white">
        {/* Top Floating Controls Bar */}
        <div className="absolute top-4 left-4 right-4 z-20 flex items-center justify-between pointer-events-none gap-2 flex-wrap">
          <div className="pointer-events-auto flex items-center gap-2">
            {hasAnnotated && (
              <button
                type="button"
                onClick={() => setShowAnnotations(!showAnnotations)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold backdrop-blur-md flex items-center gap-1.5 transition-all shadow-sm cursor-pointer ${
                  showAnnotations
                    ? 'bg-[#1F7A4D] text-white shadow-emerald-900/20'
                    : 'bg-white/95 text-slate-700 border border-slate-200 hover:bg-white'
                }`}
              >
                {showAnnotations ? <Eye size={14} /> : <EyeOff size={14} />}
                <span>{showAnnotations ? 'Khoanh vùng' : 'Ảnh gốc'}</span>
              </button>
            )}

          </div>

          <div className="pointer-events-auto flex items-center gap-1 bg-white/95 backdrop-blur-md p-1 rounded-xl border border-slate-200 shadow-xs">
            <button
              type="button"
              onClick={handleZoomIn}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-700 transition-colors cursor-pointer"
              title="Phóng to"
              aria-label="Phóng to"
            >
              <ZoomIn size={14} />
            </button>
            <button
              type="button"
              onClick={handleZoomOut}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-700 transition-colors cursor-pointer"
              title="Thu nhỏ"
              aria-label="Thu nhỏ"
            >
              <ZoomOut size={14} />
            </button>
            <button
              type="button"
              onClick={handleResetZoom}
              className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-700 transition-colors cursor-pointer"
              title="Đặt lại"
              aria-label="Đặt lại"
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

      </div>

      {/* Detection Cards Grid */}
      {detections.length > 1 && (
        <div className="space-y-2.5 pt-1">

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {detections.map((det, index) => {
              const cleanName = det.class_name.replace(/_/g, ' ');
              const confPct = (det.confidence * 100).toFixed(1);
              const isActive = activeDetectionIndex === index;

              return (
                <div
                  key={det.id || index}
                  onMouseEnter={() => setActiveDetectionIndex(index)}
                  onMouseLeave={() => setActiveDetectionIndex(null)}
                  className={`p-3 rounded-xl border transition-all cursor-pointer ${
                    isActive
                      ? 'bg-[#EAF5EE] border-emerald-400 shadow-sm'
                      : 'bg-white border-[#DCE5DC] hover:border-emerald-300 shadow-2xs'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold text-slate-900 truncate">{cleanName}</span>
                    <span className="text-[11px] font-mono font-bold text-[#1F7A4D] shrink-0">{confPct}%</span>
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

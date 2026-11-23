import { useRef, useState, type ChangeEvent, type DragEvent, type ReactNode } from 'react';
import { Camera, ImageUp, X } from 'lucide-react';

interface ViewfinderProps {
  leafLabel: string;
  maxUploadMb: number;
  previewUrl: string | null;
  scanning: boolean;
  onFile: (file: File) => void;
  onClear: () => void;
  children?: ReactNode;
}

function LeafGuide() {
  return (
    <svg viewBox="0 0 120 120" className="w-28 h-28 sm:w-32 sm:h-32" aria-hidden="true">
      <path
        d="M24 96C24 52 52 24 98 20c-3 46-30 74-74 76Z"
        fill="none"
        stroke="#5EE6A0"
        strokeOpacity="0.55"
        strokeWidth="2"
        strokeDasharray="5 6"
      />
      <path d="M26 94 76 44M48 72l-2-18M60 60l16 2M40 80l-14-2" stroke="#5EE6A0" strokeOpacity="0.35" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

/** Camera-style capture area: drop/choose/shoot a leaf photo, then preview it inside the same frame. */
export function Viewfinder({ leafLabel, maxUploadMb, previewUrl, scanning, onFile, onClear, children }: ViewfinderProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const cameraInputRef = useRef<HTMLInputElement | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  const handleInput = (e: ChangeEvent<HTMLInputElement>) => {
    const picked = e.target.files?.[0];
    if (picked) onFile(picked);
    e.target.value = '';
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    const dropped = e.dataTransfer.files?.[0];
    if (dropped) onFile(dropped);
  };

  return (
    <div
      className="viewfinder min-h-[340px] sm:min-h-[440px] flex flex-col"
      data-drag={isDragOver}
      onDragOver={(e) => {
        e.preventDefault();
        if (!previewUrl) setIsDragOver(true);
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={previewUrl ? undefined : handleDrop}
    >
      <span className="vf-corner tl" />
      <span className="vf-corner tr" />
      <span className="vf-corner bl" />
      <span className="vf-corner br" />

      <input ref={fileInputRef} type="file" accept="image/*" onChange={handleInput} className="hidden" />
      <input ref={cameraInputRef} type="file" accept="image/*" capture="environment" onChange={handleInput} className="hidden" />

      {previewUrl ? (
        <div className="relative flex-1 flex items-center justify-center p-8 sm:p-10">
          <img
            src={previewUrl}
            alt={`Ảnh ${leafLabel} vừa chọn`}
            className="max-h-[400px] w-auto max-w-full object-contain rounded-xl"
          />
          {scanning && <span className="vf-scanline" aria-hidden="true" />}
          {!scanning && (
            <button
              type="button"
              onClick={onClear}
              className="absolute top-5 right-5 w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors cursor-pointer"
              title="Bỏ ảnh này"
              aria-label="Bỏ ảnh này"
            >
              <X size={18} />
            </button>
          )}
        </div>
      ) : (
        <div className="flex-1 flex flex-col items-center justify-center text-center px-6 py-12 gap-5">
          <LeafGuide />
          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => cameraInputRef.current?.click()}
              title={`Chụp ${leafLabel} · tối đa ${maxUploadMb} MB`}
              className="inline-flex items-center gap-2 h-12 px-6 rounded-xl bg-mint text-forest font-bold text-sm hover:bg-[#7BEDB3] transition-colors cursor-pointer"
            >
              <Camera size={18} />
              Chụp
            </button>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="inline-flex items-center gap-2 h-12 px-6 rounded-xl border border-white/25 text-white font-semibold text-sm hover:bg-white/10 transition-colors cursor-pointer"
            >
              <ImageUp size={18} />
              Chọn ảnh
            </button>
          </div>
        </div>
      )}

      {children}
    </div>
  );
}

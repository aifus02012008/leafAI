import { Check, Clock, Leaf } from 'lucide-react';
import type { Crop, CropCode } from '../types';

interface CropSelectorProps {
  crops: readonly Crop[];
  value: CropCode;
  onChange: (code: CropCode) => void;
  disabled?: boolean;
}

/** Step 1 of the diagnosis flow: pick which crop the leaf belongs to. */
export function CropSelector({ crops, value, onChange, disabled = false }: CropSelectorProps) {
  return (
    <fieldset className="clean-card p-5 sm:p-6 rounded-3xl space-y-3.5" disabled={disabled}>
      <legend className="sr-only">Chọn loại cây trồng</legend>
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
          <Leaf size={14} className="text-[#15803D]" />
          Bước 1 · Chọn loại cây
        </span>
      </div>

      <div role="radiogroup" className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {crops.map((crop) => {
          const selected = crop.code === value;
          const unavailable = !crop.is_available;
          return (
            <button
              key={crop.code}
              type="button"
              role="radio"
              aria-checked={selected}
              aria-disabled={unavailable}
              disabled={disabled || unavailable}
              onClick={() => onChange(crop.code)}
              title={unavailable ? `Mô hình cho cây ${crop.name_vi} đang được phát triển` : crop.scientific_name}
              className={`relative text-left p-3 rounded-2xl border transition-all min-h-[76px] ${
                selected
                  ? 'border-emerald-500 bg-[#F0FDF4] shadow-xs ring-2 ring-emerald-200'
                  : unavailable
                    ? 'border-slate-200 bg-slate-50/70 opacity-70 cursor-not-allowed'
                    : 'border-[#E2EFE7] bg-white/80 hover:border-emerald-300 hover:bg-white cursor-pointer'
              }`}
            >
              {selected && (
                <span className="absolute top-2 right-2 w-5 h-5 rounded-full bg-[#15803D] text-white flex items-center justify-center">
                  <Check size={12} strokeWidth={3} />
                </span>
              )}
              <span className="block text-sm font-bold text-slate-900 pr-6">{crop.name_vi}</span>
              <span className="block text-[11px] italic text-slate-500 truncate">{crop.scientific_name}</span>
              {unavailable && (
                <span className="mt-1.5 inline-flex items-center gap-1 text-[10px] font-bold text-amber-700 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5">
                  <Clock size={10} />
                  Sắp ra mắt
                </span>
              )}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}

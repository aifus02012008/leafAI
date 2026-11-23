import { Check } from 'lucide-react';
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
    <fieldset disabled={disabled}>
      <legend className="sr-only">Loại cây</legend>

      <div role="radiogroup" aria-label="Loại cây" className="flex flex-wrap gap-2">
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
              title={unavailable ? `AI cho cây ${crop.name_vi} đang được huấn luyện` : crop.scientific_name}
              className={`inline-flex items-center gap-2 h-11 pl-3 pr-4 rounded-full border text-sm font-semibold transition-colors ${
                selected
                  ? 'bg-forest border-forest text-white'
                  : unavailable
                    ? 'bg-white/50 border-dashed border-[#C5D1C6] text-ink/55 cursor-not-allowed'
                    : 'bg-white border-line text-ink hover:border-leaf cursor-pointer'
              }`}
            >
              <span
                className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${
                  selected ? 'bg-mint text-forest' : 'border border-current opacity-40'
                }`}
                aria-hidden="true"
              >
                {selected && <Check size={12} strokeWidth={3} />}
              </span>
              {crop.name_vi}
              {unavailable && (
                <span className="text-[10px] font-bold uppercase tracking-wide rounded-full bg-sun-wash text-[#8A6A00] px-2 py-0.5">
                  Sắp có
                </span>
              )}
            </button>
          );
        })}
      </div>
    </fieldset>
  );
}

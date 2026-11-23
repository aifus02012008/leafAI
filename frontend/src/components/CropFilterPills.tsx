import type { Crop, CropCode } from '../types';

interface CropFilterPillsProps {
  crops: readonly Crop[];
  value: CropCode | null;
  onChange: (code: CropCode | null) => void;
  label?: string;
}

/** "Tất cả / Chè / Sầu riêng / ..." filter used by the library and history pages. */
export function CropFilterPills({ crops, value, onChange, label = 'Lọc theo cây trồng' }: CropFilterPillsProps) {
  const options: { code: CropCode | null; name: string }[] = [
    { code: null, name: 'Tất cả cây' },
    ...crops.map((c) => ({ code: c.code, name: c.name_vi })),
  ];

  return (
    <div
      role="group"
      aria-label={label}
      className="flex flex-wrap items-center gap-1.5 text-xs bg-white/60 p-1.5 rounded-2xl border border-[#E2EFE7]"
    >
      {options.map((opt) => {
        const active = opt.code === value;
        return (
          <button
            key={opt.code ?? 'all'}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(opt.code)}
            className={`px-3.5 py-1.5 rounded-xl font-bold transition-all cursor-pointer ${
              active ? 'bg-[#15803D] text-white shadow-xs' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            {opt.name}
          </button>
        );
      })}
    </div>
  );
}

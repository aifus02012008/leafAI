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
    { code: null, name: 'Mọi cây' },
    ...crops.map((c) => ({ code: c.code, name: c.name_vi })),
  ];

  return (
    <div
      role="group"
      aria-label={label}
      className="flex flex-wrap items-center gap-1 text-xs bg-white p-1 rounded-xl border border-[#DCE5DC]"
    >
      {options.map((opt) => {
        const active = opt.code === value;
        return (
          <button
            key={opt.code ?? 'all'}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(opt.code)}
            className={`px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
              active ? 'bg-[#1F7A4D] text-white shadow-xs' : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            {opt.name}
          </button>
        );
      })}
    </div>
  );
}

import { Focus, Sun, Leaf, Square } from 'lucide-react';

const TIPS = [
  { icon: Leaf, label: 'Một lá, cận cảnh' },
  { icon: Sun, label: 'Đủ sáng' },
  { icon: Focus, label: 'Rõ nét' },
  { icon: Square, label: 'Nền trơn' },
] as const;

/** Shown before the first diagnosis: four icon hints for a usable photo. */
export function PhotoTips() {
  return (
    <ul className="grid grid-cols-2 gap-3" aria-label="Mẹo chụp">
      {TIPS.map(({ icon: Icon, label }) => (
        <li key={label} className="clean-card p-4 flex flex-col items-center gap-2.5 text-center">
          <span className="w-11 h-11 rounded-2xl bg-leaf-wash text-leaf flex items-center justify-center">
            <Icon size={20} />
          </span>
          <span className="text-sm font-semibold text-ink">{label}</span>
        </li>
      ))}
    </ul>
  );
}

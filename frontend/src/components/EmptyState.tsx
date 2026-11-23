import type { ReactNode } from 'react';
import { Leaf } from 'lucide-react';

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="clean-card p-8 flex flex-col items-center justify-center text-center space-y-3.5 border border-dashed border-[#DCE5DC] bg-white font-sans">
      <div className="w-14 h-14 rounded-2xl bg-[#EAF5EE] border border-emerald-200/80 flex items-center justify-center text-[#1F7A4D] shadow-2xs">
        {icon || <Leaf size={24} />}
      </div>

      <div className="max-w-sm space-y-1">
        <h3 className="text-sm sm:text-base font-bold text-slate-900 font-display">{title}</h3>
        {description && <p className="text-xs text-slate-500 leading-relaxed">{description}</p>}
      </div>

      {action && <div className="pt-2">{action}</div>}
    </div>
  );
}

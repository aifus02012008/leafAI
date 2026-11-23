import type { ReactNode } from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: ReactNode;
  trend?: string;
  variant?: 'forest' | 'amber' | 'emerald' | 'teal' | 'purple' | 'pink';
}

export function StatCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  variant = 'forest'
}: StatCardProps) {
  const variantStyles = {
    forest: {
      iconBg: 'bg-[#EAF5EE] text-[#1F7A4D] border border-emerald-200/80',
      badgeColor: 'text-[#1F7A4D] bg-[#EAF5EE] border-emerald-200',
    },
    emerald: {
      iconBg: 'bg-emerald-50 text-emerald-700 border border-emerald-200',
      badgeColor: 'text-emerald-700 bg-emerald-50 border-emerald-200',
    },
    amber: {
      iconBg: 'bg-amber-50 text-amber-700 border border-amber-200',
      badgeColor: 'text-amber-800 bg-amber-50 border-amber-200',
    },
    teal: {
      iconBg: 'bg-teal-50 text-teal-700 border border-teal-200',
      badgeColor: 'text-teal-700 bg-teal-50 border-teal-200',
    },
    // Backwards compatibility for previous variant names
    purple: {
      iconBg: 'bg-[#EAF5EE] text-[#1F7A4D] border border-emerald-200/80',
      badgeColor: 'text-[#1F7A4D] bg-[#EAF5EE] border-emerald-200',
    },
    pink: {
      iconBg: 'bg-amber-50 text-amber-700 border border-amber-200',
      badgeColor: 'text-amber-800 bg-amber-50 border-amber-200',
    },
  }[variant] || {
    iconBg: 'bg-[#EAF5EE] text-[#1F7A4D] border border-emerald-200/80',
    badgeColor: 'text-[#1F7A4D] bg-[#EAF5EE] border-emerald-200',
  };

  return (
    <div className="clean-card clean-card-hover p-5 flex flex-col justify-between min-h-[170px] border border-[#DCE5DC] bg-white">
      <div className="flex items-center justify-between">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-500 font-sans">
          {title}
        </span>
        <div className={`p-3 rounded-xl ${variantStyles.iconBg} shadow-2xs`}>
          {icon}
        </div>
      </div>

      <div className="mt-4 flex items-baseline gap-3">
        <span className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#10201A] font-display">
          {value}
        </span>
        {trend && (
          <span className={`text-[11px] font-bold px-2 py-0.5 rounded-md border ${variantStyles.badgeColor} font-mono`}>
            {trend}
          </span>
        )}
      </div>

      {subtitle && (
        <p className="mt-2 text-xs text-slate-500 font-medium leading-relaxed">
          {subtitle}
        </p>
      )}
    </div>
  );
}

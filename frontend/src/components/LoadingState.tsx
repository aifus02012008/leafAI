import { Loader2 } from 'lucide-react';

interface LoadingStateProps {
  message?: string;
  size?: number;
}

export function LoadingState({ message = 'Đang tải dữ liệu...', size = 32 }: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-12 space-y-3 font-sans">
      <div className="relative">
        <Loader2 size={size} className="text-[#1F7A4D] animate-spin" />
        <div className="absolute inset-0 blur-md bg-emerald-400/20 rounded-full animate-pulse" />
      </div>
      <p className="text-xs sm:text-sm font-semibold text-slate-500 tracking-wide">
        {message}
      </p>
    </div>
  );
}

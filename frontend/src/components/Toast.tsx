import { useState, useEffect } from 'react';
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info';

interface ToastItem {
  id: string;
  type: ToastType;
  message: string;
}

let toastNotifier: ((type: ToastType, message: string) => void) | null = null;

export function showToast(type: ToastType, message: string) {
  if (toastNotifier) {
    toastNotifier(type, message);
  }
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  useEffect(() => {
    toastNotifier = (type: ToastType, message: string) => {
      const id = `${Date.now()}_${Math.random().toString(36).substring(2, 7)}`;
      setToasts((prev) => [...prev, { id, type, message }]);

      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4500);
    };

    return () => {
      toastNotifier = null;
    };
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <div className="fixed top-5 right-5 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none font-sans">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`pointer-events-auto flex items-start gap-2.5 p-3.5 rounded-2xl border shadow-lg backdrop-blur-md transition-all duration-200 animate-in fade-in slide-in-from-top-2 ${
            t.type === 'success'
              ? 'bg-white/95 border-emerald-300 text-slate-900 shadow-emerald-900/5'
              : t.type === 'error'
              ? 'bg-white/95 border-red-300 text-slate-900 shadow-red-900/5'
              : 'bg-white/95 border-emerald-200 text-slate-900 shadow-emerald-900/5'
          }`}
        >
          {t.type === 'success' && <CheckCircle2 size={17} className="text-emerald-600 mt-0.5 shrink-0" />}
          {t.type === 'error' && <AlertCircle size={17} className="text-red-500 mt-0.5 shrink-0" />}
          {t.type === 'info' && <Info size={17} className="text-[#1F7A4D] mt-0.5 shrink-0" />}

          <div className="flex-1 text-xs font-semibold leading-relaxed">{t.message}</div>

          <button
            type="button"
            onClick={() => removeToast(t.id)}
            aria-label="Đóng thông báo"
            className="text-slate-400 hover:text-slate-700 transition-colors cursor-pointer"
          >
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}

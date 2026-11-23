import { AlertTriangle, X } from 'lucide-react';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Xóa',
  cancelLabel = 'Hủy Bỏ',
  loading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150 font-sans"
      onClick={onCancel}
    >
      <div
        className="w-full max-w-md p-6 bg-white rounded-3xl border border-[#DCE5DC] shadow-xl relative space-y-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-red-50 border border-red-200 text-red-600 shadow-2xs">
              <AlertTriangle size={18} />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900 font-display">{title}</h3>
              <p className="text-xs text-slate-500">Vui lòng xác nhận hành động của bạn</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onCancel}
            aria-label="Đóng hộp thoại"
            className="w-8 h-8 rounded-xl bg-white text-slate-400 hover:text-slate-700 flex items-center justify-center transition-colors cursor-pointer border border-slate-200 shadow-2xs"
          >
            <X size={15} />
          </button>
        </div>

        <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
          {message}
        </p>

        <div className="pt-2 flex items-center justify-end gap-2.5 border-t border-[#DCE5DC]">
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="btn-secondary text-xs py-2 px-3.5"
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-red-600 hover:bg-red-700 text-white transition-all shadow-xs disabled:opacity-50 cursor-pointer"
          >
            {loading ? 'Đang xử lý...' : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

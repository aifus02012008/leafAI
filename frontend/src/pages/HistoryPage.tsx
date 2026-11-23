import { useState, useEffect, useRef } from 'react';
import {
  History,
  Search,
  Trash2,
  Eye,
} from 'lucide-react';
import { apiGetHistory, apiGetHistoryDetail, apiDeleteHistory } from '../api/diagnosis';
import { resolveMediaUrl } from '../api/client';
import { HistoryDetailModal } from '../components/HistoryDetailModal';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { LoadingState } from '../components/LoadingState';
import { EmptyState } from '../components/EmptyState';
import { showToast } from '../components/Toast';
import { CropFilterPills } from '../components/CropFilterPills';
import { useCrops } from '../hooks/useCrops';
import type { CropCode, DiagnosisListItem, DiagnosisResult } from '../types';

export function HistoryPage() {
  const [items, setItems] = useState<DiagnosisListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [cropFilter, setCropFilter] = useState<CropCode | null>(null);
  const { crops, cropName } = useCrops();

  // Modals state
  const [selectedDiagnosis, setSelectedDiagnosis] = useState<DiagnosisResult | null>(null);
  const [deleteTargetId, setDeleteTargetId] = useState<number | null>(null);
  const [deleting, setDeleting] = useState<boolean>(false);

  const requestSeq = useRef(0);

  const fetchHistory = () => {
    const seq = ++requestSeq.current; // only the latest request may update state
    setLoading(true);
    apiGetHistory(statusFilter, search, cropFilter)
      .then((data) => {
        if (seq === requestSeq.current) setItems(data);
      })
      .catch(console.error)
      .finally(() => {
        if (seq === requestSeq.current) setLoading(false);
      });
  };

  useEffect(() => {
    fetchHistory();
  }, [statusFilter, cropFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchHistory();
  };

  const handleOpenDetail = async (id: number) => {
    try {
      const detail = await apiGetHistoryDetail(id);
      setSelectedDiagnosis(detail);
    } catch {
      showToast('error', 'Không thể tải chi tiết bản ghi chẩn đoán.');
    }
  };

  const handleConfirmDelete = async () => {
    if (!deleteTargetId) return;

    setDeleting(true);
    try {
      await apiDeleteHistory(deleteTargetId);
      showToast('success', 'Đã xóa bản ghi chẩn đoán và tệp hình ảnh liên quan.');
      setItems((prev) => prev.filter((item) => item.id !== deleteTargetId));
      if (selectedDiagnosis?.id === deleteTargetId) {
        setSelectedDiagnosis(null);
      }
      setDeleteTargetId(null);
    } catch (err: any) {
      showToast('error', err.response?.data?.detail || 'Xóa bản ghi thất bại.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search + filters in one toolbar */}
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 min-w-0">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm bệnh, ngày…"
            className="input-clean pl-10 py-2.5 text-xs sm:text-sm"
          />
        </form>

        <CropFilterPills crops={crops} value={cropFilter} onChange={setCropFilter} />
        <div className="flex flex-wrap items-center gap-1 text-xs bg-white p-1 rounded-xl border border-[#DCE5DC]">
          {[
            { id: 'all', label: 'Tất cả' },
            { id: 'detected', label: 'Có bệnh' },
            { id: 'no_detection', label: 'Khoẻ' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setStatusFilter(tab.id)}
              className={`px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
                statusFilter === tab.id
                  ? 'bg-[#1F7A4D] text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* History Items List */}
      {loading ? (
        <LoadingState message="Đang tải…" />
      ) : items.length > 0 ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {items.map((item) => {
            const dateObj = new Date(item.created_at);
            const dateStr = dateObj.toLocaleDateString('vi-VN');
            const timeStr = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const cleanPrimary = item.primary_disease
              ? item.primary_disease.replace('Tomato___', '').replace(/_/g, ' ')
              : item.status === 'detected'
              ? 'Có bệnh'
              : 'Lá khoẻ';

            return (
              <div key={item.id} className="clean-card clean-card-hover p-3 flex items-center gap-3 group">
                <button
                  type="button"
                  onClick={() => handleOpenDetail(item.id)}
                  className="flex items-center gap-3 min-w-0 flex-1 text-left cursor-pointer"
                  title="Xem chi tiết"
                >
                  <img
                    src={resolveMediaUrl(item.original_image_url)}
                    alt={`Lá ${cropName(item.crop_code).toLowerCase()}`}
                    className="w-14 h-14 rounded-xl object-cover bg-slate-100 shrink-0"
                  />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-bold text-slate-900 group-hover:text-[#1F7A4D] transition-colors truncate">
                      {cleanPrimary}
                    </p>
                    <p className="flex flex-wrap items-center gap-x-2 text-xs text-slate-500 mt-0.5">
                      <span className="font-semibold text-[#0F2A20]">{cropName(item.crop_code)}</span>
                      <span className="font-mono">{dateStr} {timeStr}</span>
                      {item.max_confidence !== null && (
                        <span className="font-mono font-bold text-[#1F7A4D]">{(item.max_confidence * 100).toFixed(0)}%</span>
                      )}
                    </p>
                  </div>
                </button>
                <span
                  className={`w-2.5 h-2.5 rounded-full shrink-0 ${item.status === 'detected' ? 'bg-sun' : 'bg-mint'}`}
                  title={item.status === 'detected' ? 'Có bệnh' : 'Khoẻ'}
                  aria-label={item.status === 'detected' ? 'Có bệnh' : 'Khoẻ'}
                />
                <button
                  type="button"
                  onClick={() => handleOpenDetail(item.id)}
                  className="w-9 h-9 rounded-xl text-slate-500 hover:text-[#1F7A4D] hover:bg-[#EAF5EE] hidden sm:flex items-center justify-center transition-colors cursor-pointer"
                  title="Xem chi tiết"
                  aria-label="Xem chi tiết"
                >
                  <Eye size={16} />
                </button>
                <button
                  type="button"
                  onClick={() => setDeleteTargetId(item.id)}
                  className="w-9 h-9 rounded-xl text-red-600 hover:bg-red-50 flex items-center justify-center transition-colors cursor-pointer"
                  title="Xóa"
                  aria-label="Xóa"
                >
                  <Trash2 size={15} />
                </button>
              </div>
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon={<History size={26} className="text-[#1F7A4D]" />}
          title="Chưa có lượt quét"
        />
      )}

      {/* Record Inspection Modal */}
      <HistoryDetailModal
        diagnosis={selectedDiagnosis}
        onClose={() => setSelectedDiagnosis(null)}
        onDeleteRequest={(id) => setDeleteTargetId(id)}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={deleteTargetId !== null}
        title="Xóa Bản Ghi Chẩn Đoán?"
        message="Không khôi phục được."
        confirmLabel="Xác Nhận Xóa"
        cancelLabel="Hủy Bỏ"
        loading={deleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteTargetId(null)}
      />
    </div>
  );
}

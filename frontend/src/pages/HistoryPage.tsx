import { useState, useEffect, useRef } from 'react';
import {
  History,
  Search,
  Trash2,
  Eye,
  Clock,
  Crosshair,
  Leaf
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
    <div className="space-y-8 sm:space-y-10">
      {/* Title Header */}
      <div className="space-y-1.5">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#F0FDF4] border border-emerald-200/80 text-xs font-bold text-[#15803D]">
          <Leaf size={13} className="text-[#15803D]" />
          <span>Hồ Sơ Chẩn Đoán Đã Thực Hiện</span>
        </div>
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[#0F172A] tracking-tight font-['Space_Grotesk']">
          Lịch Sử Chẩn Đoán <span className="text-gradient">Bệnh Lá</span>
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 max-w-2xl leading-relaxed">
          Xem lại, tra cứu và quản lý các kết quả nhận diện bệnh hại trên lá cây trồng, hộp định vị tổn thương và điểm số tin cậy.
        </p>
      </div>

      <CropFilterPills crops={crops} value={cropFilter} onChange={setCropFilter} />

      {/* Filter and Search Bar Card */}
      <div className="clean-card p-5 sm:p-6 rounded-3xl flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 shadow-xs">
        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-lg">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm kiếm theo tên bệnh, ngày..."
            className="input-clean pl-10 py-2.5 text-xs sm:text-sm"
          />
        </form>

        {/* Status Category Pills */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs bg-white/60 p-1.5 rounded-2xl border border-[#E2EFE7]">
          {[
            { id: 'all', label: 'Tất Cả' },
            { id: 'detected', label: 'Bệnh Phát Hiện' },
            { id: 'no_detection', label: 'Không Phát Hiện' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setStatusFilter(tab.id)}
              className={`px-3.5 py-1.5 rounded-xl font-bold transition-all cursor-pointer ${
                statusFilter === tab.id
                  ? 'bg-[#15803D] text-white shadow-xs'
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
        <LoadingState message="Đang tải lịch sử chẩn đoán của bạn..." />
      ) : items.length > 0 ? (
        <div className="space-y-4">
          {items.map((item) => {
            const dateObj = new Date(item.created_at);
            const dateStr = dateObj.toLocaleDateString('vi-VN');
            const timeStr = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            const cleanPrimary = item.primary_disease
              ? item.primary_disease.replace('Tomato___', '').replace(/_/g, ' ')
              : item.status === 'detected'
              ? 'Đã Phát Hiện Bệnh'
              : 'Lá Khỏe Mạnh / Không Có Bệnh';

            return (
              <div
                key={item.id}
                className="clean-card clean-card-hover p-4 sm:p-5 rounded-3xl flex flex-col sm:flex-row sm:items-center justify-between gap-4 group shadow-xs"
              >
                <div className="flex items-center gap-4 min-w-0">
                  {/* Thumbnail */}
                  <img
                    src={resolveMediaUrl(item.original_image_url)}
                    alt={`Lá ${cropName(item.crop_code).toLowerCase()}`}
                    className="w-16 h-16 sm:w-18 sm:h-18 rounded-2xl object-cover bg-slate-100 border border-[#E2EFE7] shrink-0"
                  />

                  {/* Info */}
                  <div className="min-w-0 flex-1 space-y-1.5">
                    <h4 className="text-sm sm:text-base font-bold text-slate-900 group-hover:text-[#15803D] transition-colors truncate font-['Space_Grotesk']">
                      {cleanPrimary}
                    </h4>

                    <div className="flex flex-wrap items-center gap-2 sm:gap-3 text-xs text-slate-500 font-mono">
                      <span className="font-sans font-bold text-[#14532D] px-2 py-0.5 rounded-md bg-emerald-50 border border-emerald-200">
                        {cropName(item.crop_code)}
                      </span>
                      <span className="flex items-center gap-1 font-medium text-slate-600">
                        <Clock size={13} className="text-[#15803D]" />
                        {dateStr} | {timeStr}
                      </span>

                      {item.max_confidence !== null && (
                        <span className="text-[#15803D] font-bold px-2 py-0.5 rounded-md bg-[#F0FDF4] border border-emerald-200">
                          Độ tin cậy: {(item.max_confidence * 100).toFixed(1)}%
                        </span>
                      )}

                      <span className="flex items-center gap-1 text-slate-500 font-medium">
                        <Crosshair size={13} className="text-teal-600" />
                        {item.detection_count} Vùng Bệnh
                      </span>
                    </div>
                  </div>
                </div>

                {/* Status & Actions */}
                <div className="flex items-center gap-2.5 self-end sm:self-center shrink-0">
                  <span
                    className={`text-xs font-semibold px-3 py-1 rounded-full font-mono ${
                      item.status === 'detected'
                        ? 'bg-amber-50 text-amber-800 border border-amber-200'
                        : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    }`}
                  >
                    {item.status === 'detected' ? 'Có Bệnh' : 'Khỏe Mạnh'}
                  </span>

                  <button
                    type="button"
                    onClick={() => handleOpenDetail(item.id)}
                    className="btn-secondary text-xs flex items-center gap-1.5 py-2 px-3.5"
                    title="Xem chi tiết kiểm tra"
                  >
                    <Eye size={14} />
                    <span>Xem Chi Tiết</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setDeleteTargetId(item.id)}
                    className="w-9 h-9 rounded-xl bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 flex items-center justify-center transition-colors cursor-pointer shadow-2xs"
                    title="Xóa Bản Ghi"
                    aria-label="Xóa Bản Ghi"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <EmptyState
          icon={<History size={26} className="text-[#15803D]" />}
          title="Chưa có bản ghi chẩn đoán nào"
          description="Bạn chưa thực hiện lượt chẩn đoán nào hoặc không có bản ghi nào khớp với bộ lọc."
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
        message="Hành động này sẽ xóa vĩnh viễn mục lịch sử chẩn đoán này và loại bỏ an toàn các tệp hình ảnh tương ứng khỏi máy chủ. Thao tác này không thể hoàn tác."
        confirmLabel="Xác Nhận Xóa"
        cancelLabel="Hủy Bỏ"
        loading={deleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setDeleteTargetId(null)}
      />
    </div>
  );
}

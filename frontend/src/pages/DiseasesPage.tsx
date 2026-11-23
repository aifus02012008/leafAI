import { useState, useEffect } from 'react';
import { Search, BookOpen } from 'lucide-react';
import { apiGetDiseases, apiGetDiseaseDetail } from '../api/diseases';
import { DiseaseCard } from '../components/DiseaseCard';
import { DiseaseDetailModal } from '../components/DiseaseDetailModal';
import { LoadingState } from '../components/LoadingState';
import { EmptyState } from '../components/EmptyState';
import { CropFilterPills } from '../components/CropFilterPills';
import { useCrops } from '../hooks/useCrops';
import type { CropCode, Disease } from '../types';

export function DiseasesPage() {
  const [diseases, setDiseases] = useState<Disease[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [cropFilter, setCropFilter] = useState<CropCode | null>(null);
  const [selectedDisease, setSelectedDisease] = useState<Disease | null>(null);
  const { crops } = useCrops();

  useEffect(() => {
    let active = true; // ignore responses from superseded filter changes
    setLoading(true);
    apiGetDiseases(search, cropFilter)
      .then((data) => {
        if (active) setDiseases(data);
      })
      .catch(console.error)
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [search, cropFilter]);

  const handleSelectDisease = async (item: Disease) => {
    setSelectedDisease(item);
    try {
      const fullDetail = await apiGetDiseaseDetail(item.id);
      setSelectedDisease(fullDetail);
    } catch (err) {
      console.error('Failed to load disease detail:', err);
    }
  };

  return (
    <div className="space-y-8 sm:space-y-10">

      <CropFilterPills crops={crops} value={cropFilter} onChange={setCropFilter} />

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-lg">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm bệnh…"
            className="input-clean pl-10 py-2.5 text-xs sm:text-sm shadow-2xs"
          />
        </div>

        <div className="flex items-center gap-3 text-xs font-semibold text-slate-600">
          <span className="px-3.5 py-2 rounded-xl bg-white/85 border border-[#DCE5DC] shadow-2xs font-mono text-[#1F7A4D]">
            {diseases.length} Tác Nhân Bệnh Đã Hiệu Chuẩn
          </span>
        </div>
      </div>

      {/* Disease Cards Grid */}
      {loading ? (
        <LoadingState message="Đang tải…" />
      ) : diseases.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-7">
          {diseases.map((d) => (
            <DiseaseCard
              key={d.id}
              disease={d}
              onSelect={handleSelectDisease}
            />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={<BookOpen size={24} className="text-[#1F7A4D]" />}
          title="Không tìm thấy"
          action={
            <button
              type="button"
              onClick={() => {
                setSearch('');
                setCropFilter(null);
              }}
              className="btn-primary text-xs"
            >
              Xóa Bộ Lọc
            </button>
          }
        />
      )}

      {/* Detailed Modal */}
      <DiseaseDetailModal
        disease={selectedDisease}
        onClose={() => setSelectedDisease(null)}
      />
    </div>
  );
}

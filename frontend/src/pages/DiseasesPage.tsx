import { useState, useEffect } from 'react';
import { Search, BookOpen, Leaf } from 'lucide-react';
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
      {/* Title Header */}
      <div className="space-y-1.5">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#F0FDF4] border border-emerald-200/80 text-xs font-bold text-[#15803D]">
          <Leaf size={13} className="text-[#15803D]" />
          <span>Cơ Sở Dữ Liệu Bệnh Học Lá Cây Trồng</span>
        </div>
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[#0F172A] tracking-tight font-['Space_Grotesk']">
          Bệnh Học Cây Trồng & <span className="text-gradient">Thư Viện Bệnh Hại</span>
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 max-w-2xl leading-relaxed">
          Thư viện bệnh lá chè, sầu riêng, măng cụt và chôm chôm: tác nhân gây bệnh, triệu chứng chẩn đoán và lộ trình điều trị.
        </p>
      </div>

      <CropFilterPills crops={crops} value={cropFilter} onChange={setCropFilter} />

      {/* Search & Filter Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-lg">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm kiếm bệnh hại (vd: Thán thư, Phytophthora, Đốm rong, Rầy xanh, Phấn trắng)..."
            className="input-clean pl-10 py-2.5 text-xs sm:text-sm shadow-2xs"
          />
        </div>

        <div className="flex items-center gap-3 text-xs font-semibold text-slate-600">
          <span className="px-3.5 py-2 rounded-xl bg-white/85 border border-[#E2EFE7] shadow-2xs font-mono text-[#15803D]">
            {diseases.length} Tác Nhân Bệnh Đã Hiệu Chuẩn
          </span>
        </div>
      </div>

      {/* Disease Cards Grid */}
      {loading ? (
        <LoadingState message="Đang tải danh mục bệnh học..." />
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
          icon={<BookOpen size={24} className="text-[#15803D]" />}
          title="Không tìm thấy bệnh hại phù hợp"
          description="Không tìm thấy bệnh hại nào khớp với từ khóa và loại cây đã chọn. Vui lòng thử bộ lọc khác."
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

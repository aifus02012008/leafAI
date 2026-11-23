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
  const { crops, cropName } = useCrops();
  // One section per crop, in the registry's order, so the list reads as short groups instead of one long wall.
  const groups = crops
    .map((c) => ({ code: c.code, name: cropName(c.code), items: diseases.filter((d) => d.crop_code === c.code) }))
    .filter((g) => g.items.length > 0);

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
    <div className="space-y-6">
      {/* Search & Filter Toolbar */}
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center gap-3">
        <div className="relative flex-1 min-w-0">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Tìm bệnh…"
            className="input-clean pl-10 py-2.5 text-xs sm:text-sm shadow-2xs"
          />
        </div>

        <CropFilterPills crops={crops} value={cropFilter} onChange={setCropFilter} />
        <span className="self-start lg:self-auto px-3 py-2 rounded-xl bg-white border border-[#DCE5DC] font-mono text-xs font-semibold text-[#1F7A4D] whitespace-nowrap">
          {diseases.length} bệnh
        </span>
      </div>

      {/* Disease Cards Grid */}
      {loading ? (
        <LoadingState message="Đang tải…" />
      ) : diseases.length > 0 ? (
        <div className="space-y-6">
          {groups.map((g) => (
            <section key={g.code} aria-labelledby={`crop-${g.code}`} className="space-y-3">
              <h2 id={`crop-${g.code}`} className="flex items-baseline gap-2 font-display text-base font-bold text-ink">
                {g.name}
                <span className="text-xs font-semibold text-ink/40">{g.items.length}</span>
              </h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {g.items.map((d) => (
                  <DiseaseCard key={d.id} disease={d} onSelect={handleSelectDisease} />
                ))}
              </div>
            </section>
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

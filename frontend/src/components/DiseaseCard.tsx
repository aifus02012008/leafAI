import { ArrowRight, AlertTriangle, ListChecks, Leaf } from 'lucide-react';
import type { Disease } from '../types';
import { useCrops } from '../hooks/useCrops';

interface DiseaseCardProps {
  disease: Disease;
  onSelect: (disease: Disease) => void;
}

export function DiseaseCard({ disease, onSelect }: DiseaseCardProps) {
  const cleanClass = disease.class_name.replace('Tomato___', '').replace(/_/g, ' ');
  const { crops } = useCrops();
  const crop = crops.find((c) => c.code === disease.crop_code);

  return (
    <div className="clean-card clean-card-hover p-6 sm:p-7 rounded-3xl flex flex-col justify-between group bg-white border border-[#DCE5DC] shadow-xs">
      <div>
        {/* Top Header */}
        <div className="flex items-start justify-between gap-3 mb-3.5">
          <div className="w-11 h-11 rounded-xl bg-[#EAF5EE] border border-emerald-200/80 flex items-center justify-center text-[#1F7A4D] group-hover:scale-105 transition-transform duration-200 shadow-2xs">
            <Leaf size={20} />
          </div>
          <span className="text-[11px] font-mono tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 font-semibold border border-emerald-200">
            {crop ? `${crop.name_vi} · ${crop.scientific_name}` : 'Camellia sinensis'}
          </span>
        </div>

        {/* Disease Names */}
        <h3 className="text-base font-bold text-slate-900 group-hover:text-[#1F7A4D] transition-colors line-clamp-1 font-display">
          {disease.display_name}
        </h3>
        <p className="text-xs text-[#1F7A4D] font-mono font-medium mt-0.5 truncate">
          Tác nhân / Phân loại: {cleanClass}
        </p>

        {/* Diagnostic Symptoms preview */}
        {disease.symptoms && (
          <div className="mt-3.5 p-3 rounded-xl bg-amber-50/50 border border-amber-200/70">
            <div className="flex items-center gap-1.5 text-xs font-bold text-amber-900 mb-1">
              <AlertTriangle size={13} className="text-amber-600" />
              <span>Triệu chứng</span>
            </div>
            <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
              {disease.symptoms}
            </p>
          </div>
        )}

        {/* Unified Complete Treatment Timeline Badge */}
        <div className="mt-3.5 flex flex-wrap gap-2">
          <span className="text-[11px] font-semibold px-2.5 py-1 rounded-lg bg-[#EAF5EE] text-[#1F7A4D] flex items-center gap-1.5 border border-emerald-200">
            <ListChecks size={13} className="text-[#1F7A4D]" />
            Lộ Trình Điều Trị Toàn Diện
          </span>
        </div>
      </div>

      {/* Action Footer */}
      <div className="mt-5 pt-3.5 border-t border-[#DCE5DC]">
        <button
          type="button"
          onClick={() => onSelect(disease)}
          className="w-full btn-secondary text-xs py-2.5 px-4 flex items-center justify-center gap-2 group-hover:border-emerald-300 group-hover:text-[#1F7A4D]"
        >
          <span>Phác đồ</span>
          <ArrowRight size={13} className="transition-transform group-hover:translate-x-1" />
        </button>
      </div>
    </div>
  );
}

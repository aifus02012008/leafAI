import { ArrowRight } from 'lucide-react';
import type { Disease } from '../types';
import { useCrops } from '../hooks/useCrops';

interface DiseaseCardProps {
  disease: Disease;
  onSelect: (disease: Disease) => void;
}

/** Library tile: crop, disease name, a short symptom preview. The whole card opens the treatment plan. */
export function DiseaseCard({ disease, onSelect }: DiseaseCardProps) {
  const { cropName } = useCrops();

  return (
    <button
      type="button"
      onClick={() => onSelect(disease)}
      className="clean-card clean-card-hover p-4 flex flex-col gap-2 text-left group cursor-pointer"
    >
      <span className="self-start text-[11px] font-semibold px-2 py-0.5 rounded-full bg-[#EAF5EE] text-[#1F7A4D]">
        {cropName(disease.crop_code)}
      </span>
      <h3 className="text-sm font-bold text-slate-900 group-hover:text-[#1F7A4D] transition-colors line-clamp-2">
        {disease.display_name}
      </h3>
      {disease.symptoms && (
        <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">{disease.symptoms}</p>
      )}
      <span className="mt-auto pt-1 inline-flex items-center gap-1 text-xs font-bold text-[#1F7A4D]">
        Phác đồ <ArrowRight size={13} className="transition-transform group-hover:translate-x-1" />
      </span>
    </button>
  );
}

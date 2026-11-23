import { ChevronRight } from 'lucide-react';
import type { Disease } from '../types';

interface DiseaseCardProps {
  disease: Disease;
  onSelect: (disease: Disease) => void;
}

/** Compact library tile: disease name and a one-line symptom hint. The whole tile opens the treatment plan. */
export function DiseaseCard({ disease, onSelect }: DiseaseCardProps) {
  return (
    <button
      type="button"
      onClick={() => onSelect(disease)}
      className="clean-card clean-card-hover px-4 py-3 flex items-center gap-3 text-left group cursor-pointer min-w-0"
    >
      <div className="min-w-0 flex-1">
        <h3 className="text-sm font-bold text-slate-900 group-hover:text-[#1F7A4D] transition-colors truncate">
          {disease.display_name}
        </h3>
        {disease.symptoms && <p className="text-xs text-slate-500 truncate mt-0.5">{disease.symptoms}</p>}
      </div>
      <ChevronRight size={16} className="text-[#1F7A4D] shrink-0 transition-transform group-hover:translate-x-0.5" />
    </button>
  );
}

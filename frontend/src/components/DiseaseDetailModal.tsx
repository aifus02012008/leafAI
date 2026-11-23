import { useState, useEffect, useMemo } from 'react';
import {
  X,
  ShieldAlert,
  BookOpen,
  AlertCircle,
  ListChecks,
  Clock,
  Sprout,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  Info,
  Leaf,
  ShieldCheck,
  Search
} from 'lucide-react';
import type { Disease } from '../types';
import { apiGetDiseaseDetail } from '../api/diseases';
import { useCrops } from '../hooks/useCrops';

interface DiseaseDetailModalProps {
  disease: Disease | null;
  onClose: () => void;
}

interface StageContent {
  action?: string;
  monitoring?: string;
  improvement?: string;
  extraIntervention?: string;
  recoveryPeriod?: string;
  criteria?: string[];
  tissueNote?: string;
  extraLines: string[];
}

interface ParsedStage {
  stageNum: number | string;
  title: string;
  timeframe: string;
  isFinal: boolean;
  content: StageContent;
}

export function DiseaseDetailModal({ disease, onClose }: DiseaseDetailModalProps) {
  // Default to the single unified Complete Treatment Timeline view
  const [activeTab, setActiveTab] = useState<'timeline' | 'symptoms' | 'prevention' | 'all'>('timeline');
  const [currentDisease, setCurrentDisease] = useState<Disease | null>(disease);
  const { crops } = useCrops();
  const crop = crops.find((c) => c.code === (currentDisease?.crop_code ?? 'tea'));
  const cropNameVi = crop?.name_vi ?? 'Chè';
  const cropScientific = crop?.scientific_name ?? 'Camellia sinensis';
  const cropLower = cropNameVi.toLowerCase();

  // Sync disease prop and fetch full details if fields are missing
  useEffect(() => {
    setCurrentDisease(disease);
    if (disease && (!disease.treatment_steps || !disease.recovery_info)) {
      apiGetDiseaseDetail(disease.id)
        .then((full) => setCurrentDisease(full))
        .catch((err) => console.error('Failed to load full disease detail:', err));
    }
  }, [disease]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Parse structured treatment stages into chronological timeline objects
  const { emergencyNotice, stages } = useMemo(() => {
    if (!currentDisease?.treatment_steps) {
      return { emergencyNotice: null, stages: [] };
    }

    const raw = currentDisease.treatment_steps;
    let notice: string | null = null;
    let textContent = raw;

    // Check for emergency header like ⚠️ KHẨN CẤP...
    const noticeMatch = raw.match(/^(⚠️[^\n]+\n+)/);
    if (noticeMatch) {
      notice = noticeMatch[1].trim();
      textContent = raw.substring(noticeMatch[0].length);
    }

    // Split blocks on "Giai đoạn" or "Bước"
    const blocks = textContent.split(/(?=(?:Giai đoạn\s*(?:\d+|cuối)|Bước\s*\d+)\s*—)/gi).filter(Boolean);
    const parsedStages: ParsedStage[] = [];

    blocks.forEach((block, idx) => {
      const lines = block.trim().split('\n').filter((l) => l.trim().length > 0);
      if (lines.length === 0) return;

      const headerLine = lines[0];
      const isFinal = /cuối/i.test(headerLine);

      let stageNum: number | string = idx + 1;
      let title = headerLine;
      let timeframe = '';

      // Match patterns like "Giai đoạn 1 — Ngày 1: Đánh giá ban đầu..." or "Giai đoạn cuối — Đánh giá phục hồi..."
      const match = headerLine.match(/(?:Giai đoạn\s*(\d+|cuối)|Bước\s*(\d+))\s*—\s*([^:]+):?/i);
      if (match) {
        stageNum = isFinal ? 'Final' : parseInt(match[1] || match[2], 10) || idx + 1;
        const mainPart = match[3].trim();
        title = mainPart;

        // Try extracting timeframe like "Ngày 1", "Ngày 2–3", "Ngày 4–7"
        const timeMatch = mainPart.match(/^(Ngày\s*[\d–\-]+|[^\:]+)(?:\:\s*(.+))?$/i);
        if (timeMatch && timeMatch[2]) {
          timeframe = timeMatch[1].trim();
          title = timeMatch[2].trim();
        } else if (isFinal) {
          timeframe = 'Phục Hồi Hoàn Toàn';
        }
      }

      const content: StageContent = {
        extraLines: []
      };

      let currentMode: 'action' | 'monitoring' | 'improvement' | 'extraIntervention' | 'recoveryPeriod' | 'criteria' | 'tissueNote' | null = null;

      for (let i = 1; i < lines.length; i++) {
        const line = lines[i].trim();

        if (line.startsWith('• Hành động cần làm:')) {
          currentMode = 'action';
          content.action = line.replace('• Hành động cần làm:', '').trim();
        } else if (line.startsWith('• Triệu chứng cần theo dõi:')) {
          currentMode = 'monitoring';
          content.monitoring = line.replace('• Triệu chứng cần theo dõi:', '').trim();
        } else if (line.startsWith('• Dấu hiệu cải thiện:')) {
          currentMode = 'improvement';
          content.improvement = line.replace('• Dấu hiệu cải thiện:', '').trim();
        } else if (line.startsWith('• Khi nào cần can thiệp bổ sung:')) {
          currentMode = 'extraIntervention';
          content.extraIntervention = line.replace('• Khi nào cần can thiệp bổ sung:', '').trim();
        } else if (line.startsWith('• Thời gian phục hồi ước tính:')) {
          currentMode = 'recoveryPeriod';
          content.recoveryPeriod = line.replace('• Thời gian phục hồi ước tính:', '').trim();
        } else if (line.startsWith('• Tiêu chí xác định cây khỏi bệnh:')) {
          currentMode = 'criteria';
          content.criteria = [];
        } else if (line.startsWith('• Lưu ý quan trọng về phục hồi mô:') || line.startsWith('• Lưu ý phục hồi:')) {
          currentMode = 'tissueNote';
          content.tissueNote = line.replace(/^•\s*Lưu ý[^:]*:\s*/, '').trim();
        } else if (currentMode === 'criteria' && /^\d+\.\s*/.test(line)) {
          if (!content.criteria) content.criteria = [];
          content.criteria.push(line.replace(/^\d+\.\s*/, '').trim());
        } else {
          // Append continuation lines or raw items
          if (currentMode === 'action' && content.action) {
            content.action += ' ' + line.replace(/^[•\-\*]\s*/, '');
          } else if (currentMode === 'monitoring' && content.monitoring) {
            content.monitoring += ' ' + line.replace(/^[•\-\*]\s*/, '');
          } else if (currentMode === 'improvement' && content.improvement) {
            content.improvement += ' ' + line.replace(/^[•\-\*]\s*/, '');
          } else if (currentMode === 'extraIntervention' && content.extraIntervention) {
            content.extraIntervention += ' ' + line.replace(/^[•\-\*]\s*/, '');
          } else if (currentMode === 'tissueNote' && content.tissueNote) {
            content.tissueNote += ' ' + line.replace(/^[•\-\*]\s*/, '');
          } else {
            content.extraLines.push(line.replace(/^[•\-\*]\s*/, ''));
          }
        }
      }

      parsedStages.push({
        stageNum,
        title,
        timeframe,
        isFinal,
        content
      });
    });

    return { emergencyNotice: notice, stages: parsedStages };
  }, [currentDisease?.treatment_steps]);

  if (!currentDisease) return null;

  const cleanClass = currentDisease.class_name.replace('Tomato___', '').replace(/_/g, ' ');

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-150 font-['DM_Sans']"
      onClick={onClose}
    >
      <div
        className="w-full max-w-4xl lg:max-w-5xl max-h-[92vh] overflow-y-auto bg-white rounded-3xl shadow-2xl border border-[#E2EFE7] relative flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Sticky Header */}
        <div className="sticky top-0 z-20 bg-white/95 backdrop-blur-md border-b border-[#E2EFE7] px-6 py-5 sm:px-8 sm:py-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-[10px] uppercase font-mono tracking-wider px-2.5 py-0.5 rounded-full bg-[#F0FDF4] text-[#15803D] font-bold flex items-center gap-1 border border-emerald-200">
                  <Leaf size={11} className="text-[#15803D]" />
                  {cropScientific} • Cây {cropNameVi}
                </span>
                <span className="text-[10px] font-mono tracking-wider px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 font-bold border border-emerald-200">
                  Lộ Trình Điều Trị Toàn Diện
                </span>
              </div>
              <h2 className="text-xl sm:text-2xl font-extrabold text-[#0F172A] mt-1 font-['Space_Grotesk']">
                {currentDisease.display_name}
              </h2>
              <p className="text-xs text-[#15803D] font-mono font-semibold mt-0.5">
                Tác nhân / Phân loại: {cleanClass}
              </p>
            </div>

            <button
              type="button"
              onClick={onClose}
              aria-label="Đóng cửa sổ"
              className="w-9 h-9 rounded-xl bg-white hover:bg-slate-100 text-slate-500 hover:text-slate-900 border border-slate-200 flex items-center justify-center transition-colors cursor-pointer shadow-2xs shrink-0"
            >
              <X size={17} />
            </button>
          </div>

          {/* Unified Tab Navigation */}
          <div className="flex items-center gap-1.5 sm:gap-2 mt-4 pt-3 border-t border-[#E2EFE7] overflow-x-auto no-scrollbar text-xs">
            <button
              type="button"
              onClick={() => setActiveTab('timeline')}
              className={`px-3 py-1.5 rounded-xl font-bold transition-all whitespace-nowrap flex items-center gap-1.5 cursor-pointer ${
                activeTab === 'timeline'
                  ? 'bg-[#15803D] text-white shadow-xs'
                  : 'bg-white text-emerald-800 hover:bg-[#F0FDF4] border border-emerald-200'
              }`}
            >
              <ListChecks size={13} />
              Lộ Trình Điều Trị Toàn Diện
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('symptoms')}
              className={`px-3 py-1.5 rounded-xl font-bold transition-all whitespace-nowrap flex items-center gap-1.5 cursor-pointer ${
                activeTab === 'symptoms'
                  ? 'bg-[#15803D] text-white shadow-xs'
                  : 'bg-white text-amber-800 hover:bg-amber-50 border border-amber-200'
              }`}
            >
              <AlertCircle size={13} />
              Căn Nguyên & Triệu Chứng
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('prevention')}
              className={`px-3 py-1.5 rounded-xl font-bold transition-all whitespace-nowrap flex items-center gap-1.5 cursor-pointer ${
                activeTab === 'prevention'
                  ? 'bg-[#15803D] text-white shadow-xs'
                  : 'bg-white text-[#15803D] hover:bg-emerald-50 border border-emerald-200'
              }`}
            >
              <ShieldAlert size={13} />
              Phòng Ngừa & Canh Tác IPM
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('all')}
              className={`px-3 py-1.5 rounded-xl font-bold transition-all whitespace-nowrap cursor-pointer ${
                activeTab === 'all'
                  ? 'bg-[#15803D] text-white shadow-xs'
                  : 'bg-white text-slate-600 hover:bg-slate-50 border border-[#E2EFE7]'
              }`}
            >
              Tất Cả Thông Tin
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="p-6 sm:p-8 space-y-7 text-xs sm:text-sm">
          {/* =========================================================================
              EXACTLY ONE UNIFIED SECTION: COMPLETE TREATMENT TIMELINE
              ========================================================================= */}
          {(activeTab === 'timeline' || activeTab === 'all') && (
            <section className="space-y-6">
              {/* Single Section Header Banner */}
              <div className="bg-[#F0FDF4] border border-emerald-200/80 rounded-2xl p-4 sm:p-5 shadow-2xs">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-white border border-emerald-200 flex items-center justify-center text-[#15803D] shadow-2xs">
                      <ListChecks size={18} />
                    </div>
                    <div>
                      <h3 className="text-sm sm:text-base font-extrabold text-[#14532D] font-['Space_Grotesk']">
                        Lộ Trình Điều Trị Toàn Diện
                      </h3>
                      <p className="text-xs text-slate-600">
                        Quy trình can thiệp liên tục từ ngày đầu tiên nhiễm bệnh đến khi cây {cropLower} hồi phục hoàn toàn.
                      </p>
                    </div>
                  </div>
                  <span className="text-[11px] font-mono font-bold px-3 py-1 rounded-full bg-white text-[#15803D] border border-emerald-200 self-start sm:self-auto shadow-2xs">
                    {stages.length} Mốc Thời Gian
                  </span>
                </div>
              </div>

              {/* Emergency Banner if applicable */}
              {emergencyNotice && (
                <div className="bg-rose-50 border border-rose-300 rounded-2xl p-4 flex items-start gap-3 text-rose-900 font-semibold shadow-xs">
                  <AlertTriangle size={18} className="text-rose-600 shrink-0 mt-0.5" />
                  <p className="text-xs leading-relaxed">{emergencyNotice}</p>
                </div>
              )}

              {/* Chronological Vertical Timeline Track */}
              <div className="relative pl-6 sm:pl-8 space-y-6 before:content-[''] before:absolute before:left-3 sm:before:left-4 before:top-4 before:bottom-4 before:w-0.5 before:bg-emerald-200">
                {stages.map((stage, idx) => (
                  <div key={idx} className="relative group">
                    {/* Node Dot / Marker */}
                    <div
                      className={`absolute -left-6 sm:-left-8 top-1 w-6 h-6 sm:w-7 sm:h-7 rounded-full border-2 shadow-xs flex items-center justify-center text-[10px] font-black transition-all ${
                        stage.isFinal
                          ? 'bg-[#15803D] text-white border-emerald-600'
                          : 'bg-white border-[#15803D] text-[#15803D] group-hover:bg-[#15803D] group-hover:text-white'
                      }`}
                    >
                      {stage.isFinal ? <Sprout size={13} /> : idx + 1}
                    </div>

                    {/* Timeline Stage Card */}
                    <div
                      className={`rounded-2xl p-5 sm:p-6 border shadow-2xs space-y-3.5 transition-shadow ${
                        stage.isFinal
                          ? 'bg-gradient-to-br from-[#F0FDF4] via-white to-emerald-50/40 border-emerald-300 shadow-xs'
                          : 'bg-[#F8FAF9] border-[#E2EFE7] hover:shadow-xs'
                      }`}
                    >
                      {/* Stage Card Header */}
                      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-200/60 pb-2.5">
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full border ${
                              stage.isFinal
                                ? 'bg-emerald-600 text-white border-emerald-600'
                                : 'bg-emerald-50 text-[#15803D] border-emerald-200'
                            }`}
                          >
                            {stage.timeframe || `Giai đoạn ${stage.stageNum}`}
                          </span>
                          <h4 className="font-extrabold text-slate-900 text-xs sm:text-sm font-['Space_Grotesk']">
                            {stage.title}
                          </h4>
                        </div>
                      </div>

                      {/* Regular Stage Content (Days 1 to Subsequent Days) */}
                      {!stage.isFinal && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 pt-1 text-xs">
                          {/* 1. What to do (Hành động & Hoạt chất can thiệp) */}
                          {stage.content.action && (
                            <div className="bg-white p-3.5 rounded-xl border border-emerald-200/70 shadow-2xs space-y-1">
                              <span className="font-bold text-[#14532D] flex items-center gap-1.5 uppercase tracking-wider text-[11px]">
                                <ShieldCheck size={14} className="text-[#15803D]" />
                                Hành động & Hoạt chất can thiệp
                              </span>
                              <p className="text-slate-700 leading-relaxed pl-5">
                                {stage.content.action}
                              </p>
                            </div>
                          )}

                          {/* 2. What symptoms to monitor (Triệu chứng cần theo dõi) */}
                          {stage.content.monitoring && (
                            <div className="bg-white p-3.5 rounded-xl border border-amber-200/70 shadow-2xs space-y-1">
                              <span className="font-bold text-amber-900 flex items-center gap-1.5 uppercase tracking-wider text-[11px]">
                                <Search size={14} className="text-amber-600" />
                                Triệu chứng cần theo dõi
                              </span>
                              <p className="text-slate-700 leading-relaxed pl-5">
                                {stage.content.monitoring}
                              </p>
                            </div>
                          )}

                          {/* 3. What changes indicate improvement (Dấu hiệu cải thiện) */}
                          {stage.content.improvement && (
                            <div className="bg-white p-3.5 rounded-xl border border-teal-200/70 shadow-2xs space-y-1">
                              <span className="font-bold text-teal-900 flex items-center gap-1.5 uppercase tracking-wider text-[11px]">
                                <Sparkles size={14} className="text-teal-600" />
                                Dấu hiệu cải thiện
                              </span>
                              <p className="text-slate-700 leading-relaxed pl-5">
                                {stage.content.improvement}
                              </p>
                            </div>
                          )}

                          {/* 4. When additional intervention is necessary (Khi nào cần can thiệp bổ sung) */}
                          {stage.content.extraIntervention && (
                            <div className="bg-white p-3.5 rounded-xl border border-rose-200/70 shadow-2xs space-y-1">
                              <span className="font-bold text-rose-900 flex items-center gap-1.5 uppercase tracking-wider text-[11px]">
                                <AlertTriangle size={14} className="text-rose-600" />
                                Khi nào cần can thiệp bổ sung
                              </span>
                              <p className="text-slate-700 leading-relaxed pl-5">
                                {stage.content.extraIntervention}
                              </p>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Final Stage Content: Recovery Assessment, Total Duration, and Clear Criteria */}
                      {stage.isFinal && (
                        <div className="space-y-4 pt-1 text-xs">
                          {/* Estimated Recovery Period Metric Box */}
                          {stage.content.recoveryPeriod && (
                            <div className="bg-emerald-50/80 p-4 rounded-xl border border-emerald-200 flex items-center justify-between gap-4">
                              <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-xl bg-white border border-emerald-300 flex items-center justify-center text-[#15803D] shadow-2xs">
                                  <Clock size={20} />
                                </div>
                                <div>
                                  <div className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">
                                    Thời Gian Phục Hồi Ước Tính
                                  </div>
                                  <div className="text-sm sm:text-base font-extrabold text-[#14532D] font-['Space_Grotesk']">
                                    {stage.content.recoveryPeriod}
                                  </div>
                                </div>
                              </div>
                              <span className="text-[10px] font-mono font-bold px-2.5 py-1 rounded-md bg-white text-[#15803D] border border-emerald-200 hidden sm:inline-block">
                                Chu kỳ chuẩn {cropScientific}
                              </span>
                            </div>
                          )}

                          {/* Clear Criteria for Considering the Plant Recovered */}
                          {stage.content.criteria && stage.content.criteria.length > 0 && (
                            <div className="bg-white p-4 rounded-xl border border-emerald-200/90 shadow-2xs space-y-2">
                              <span className="font-extrabold text-[#14532D] flex items-center gap-1.5 uppercase tracking-wider text-xs font-['Space_Grotesk']">
                                <CheckCircle2 size={16} className="text-[#15803D]" />
                                Tiêu chuẩn xác định cây {cropLower} đã khỏi bệnh:
                              </span>
                              <ul className="space-y-2 pl-1 pt-1">
                                {stage.content.criteria.map((item, cIdx) => (
                                  <li key={cIdx} className="flex items-start gap-2.5 text-slate-700 leading-relaxed">
                                    <div className="w-4 h-4 rounded-full bg-emerald-100 text-[#15803D] flex items-center justify-center font-bold text-[10px] shrink-0 mt-0.5">
                                      {cIdx + 1}
                                    </div>
                                    <span>{item}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Biological Reality of Damaged Leaf Tissue vs New Healthy Growth */}
                          {stage.content.tissueNote && (
                            <div className="bg-amber-50/70 p-4 rounded-xl border border-amber-200 space-y-1.5 text-amber-950">
                              <span className="font-bold flex items-center gap-1.5 uppercase tracking-wider text-[11px]">
                                <Info size={15} className="text-amber-600 shrink-0" />
                                Lưu ý sinh lý phục hồi mô lá {cropLower}:
                              </span>
                              <p className="text-slate-700 leading-relaxed text-xs pl-5">
                                {stage.content.tissueNote}
                              </p>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Fallback extra items if unparsed */}
                      {stage.content.extraLines.length > 0 && (
                        <ul className="space-y-1.5 text-xs text-slate-600 pt-2 border-t border-slate-100">
                          {stage.content.extraLines.map((line, i) => (
                            <li key={i} className="flex items-start gap-2 leading-relaxed">
                              <CheckCircle2 size={13} className="text-[#15803D] shrink-0 mt-0.5" />
                              <span>{line}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* =========================================================================
              BOTANICAL PATHOLOGY & DIAGNOSTIC SYMPTOMS
              ========================================================================= */}
          {(activeTab === 'symptoms' || activeTab === 'all') && (
            <section className="space-y-5 pt-2">
              {currentDisease.description && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-2 font-['Space_Grotesk']">
                    <BookOpen size={15} className="text-[#15803D]" />
                    Tổng Quan Bệnh Học & Tác Nhân Gây Hại
                  </h4>
                  <p className="text-slate-700 leading-relaxed text-xs sm:text-sm bg-[#F8FAF9] p-4 sm:p-5 rounded-2xl border border-[#E2EFE7]">
                    {currentDisease.description}
                  </p>
                </div>
              )}

              {currentDisease.symptoms && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-amber-900 flex items-center gap-2 font-['Space_Grotesk']">
                    <AlertCircle size={15} className="text-amber-600" />
                    Dấu Hiệu & Triệu Chứng Chẩn Đoán
                  </h4>
                  <div className="text-slate-700 leading-relaxed text-xs sm:text-sm bg-amber-50/50 p-4 sm:p-5 rounded-2xl border border-amber-200/70">
                    <div className="flex items-start gap-2.5">
                      <Info size={16} className="text-amber-600 shrink-0 mt-0.5" />
                      <div className="leading-relaxed">{currentDisease.symptoms}</div>
                    </div>
                  </div>
                </div>
              )}
            </section>
          )}

          {/* =========================================================================
              PREVENTION & INTEGRATED PEST MANAGEMENT (IPM)
              ========================================================================= */}
          {(activeTab === 'prevention' || activeTab === 'all') && currentDisease.prevention && (
            <section className="space-y-2 pt-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-[#14532D] flex items-center gap-2 font-['Space_Grotesk']">
                <ShieldAlert size={15} className="text-[#15803D]" />
                Biện Pháp Canh Tác & Phòng Ngừa Tái Nhiễm IPM
              </h4>
              <div className="text-slate-700 leading-relaxed text-xs sm:text-sm bg-[#F0FDF4] p-4 sm:p-5 rounded-2xl border border-emerald-200/80 whitespace-pre-line">
                {currentDisease.prevention}
              </div>
            </section>
          )}
        </div>

        {/* Sticky Footer */}
        <div className="sticky bottom-0 z-20 p-4 sm:p-5 bg-white/95 backdrop-blur-md border-t border-[#E2EFE7] flex items-center justify-between">
          <div className="text-[11px] text-slate-500 hidden sm:flex items-center gap-1.5">
            <Leaf size={13} className="text-[#15803D]" />
            <span>Phác đồ bệnh học {cropLower} {cropScientific} • LEAF_AI</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="btn-primary text-xs px-5 py-2 ml-auto"
          >
            Đóng Cẩm Nang Bệnh Học
          </button>
        </div>
      </div>
    </div>
  );
}

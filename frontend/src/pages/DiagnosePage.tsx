import { useState, useRef, useCallback, useEffect, type ChangeEvent, type DragEvent } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  Upload,
  Camera,
  X,
  Scan,
  Loader2,
  Sparkles,
  RefreshCw,
  Layers,
  ShieldCheck,
  Droplets,
  Leaf,
  SprayCan
} from 'lucide-react';
import { apiPredict } from '../api/diagnosis';
import { BoundingBoxViewer } from '../components/BoundingBoxViewer';
import { CropSelector } from '../components/CropSelector';
import { DiagnosisFeedback } from '../components/DiagnosisFeedback';
import { FollowupVerdictCard } from '../components/FollowupVerdictCard';
import { RecordTreatmentModal } from '../components/RecordTreatmentModal';
import { resolveMediaUrl } from '../api/client';
import { useFollowupTreatment } from '../hooks/useFollowupTreatment';
import { getCurrentPosition, readRadarConsent, storeRadarConsent } from '../hooks/useGeolocation';
import { formatDate, formatNumber } from '../utils/format';
import { showToast } from '../components/Toast';
import { useCrops } from '../hooks/useCrops';
import type { CropCode, DiagnosisResult } from '../types';

const MAX_UPLOAD_MB = 10;
const CROP_STORAGE_KEY = 'leafai_last_crop';
const DEFAULT_CROP: CropCode = 'tea';

function readStoredCrop(): CropCode {
  try {
    return localStorage.getItem(CROP_STORAGE_KEY) || DEFAULT_CROP;
  } catch {
    return DEFAULT_CROP;
  }
}

function storeCrop(code: CropCode): void {
  try {
    localStorage.setItem(CROP_STORAGE_KEY, code);
  } catch {
    /* storage unavailable (private mode) — selection just won't persist */
  }
}

export function DiagnosePage() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [result, setResult] = useState<DiagnosisResult | null>(null);
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const [crop, setCrop] = useState<CropCode>(readStoredCrop);
  const { crops, loading: cropsLoading, cropName } = useCrops();
  const [searchParams] = useSearchParams();
  const followupParam = Number(searchParams.get('followup'));
  const followup = useFollowupTreatment(Number.isInteger(followupParam) && followupParam > 0 ? followupParam : null);
  const [recordOpen, setRecordOpen] = useState(false);
  const [shareToRadar, setShareToRadar] = useState<boolean>(readRadarConsent);

  // Re-photo mode: lock the crop to the treated crop.
  useEffect(() => {
    if (followup.treatment) setCrop(followup.treatment.crop_code);
  }, [followup.treatment]);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const leafLabel = `lá ${cropName(crop).toLowerCase()}`;

  // If the remembered crop is no longer available (or unknown), fall back to tea.
  useEffect(() => {
    if (cropsLoading) return;
    const current = crops.find((c) => c.code === crop);
    if (!current || !current.is_available) setCrop(DEFAULT_CROP);
  }, [crops, cropsLoading, crop]);

  const handleSelectCrop = (code: CropCode) => {
    setCrop(code);
    storeCrop(code);
    setResult(null);
  };

  const handleProcessFile = (selectedFile: File) => {
    if (!selectedFile.type.startsWith('image/')) {
      showToast('error', 'Vui lòng tải lên tệp hình ảnh hợp lệ (JPEG, PNG, WEBP).');
      return;
    }

    if (selectedFile.size > MAX_UPLOAD_MB * 1024 * 1024) {
      showToast('error', `Kích thước ảnh vượt quá giới hạn tối đa ${MAX_UPLOAD_MB}MB.`);
      return;
    }

    setFile(selectedFile);
    setPreviewUrl(URL.createObjectURL(selectedFile));
    setResult(null);
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleProcessFile(e.target.files[0]);
    }
  };

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleProcessFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleClear = () => {
    setFile(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setResult(null);
    followup.reset();
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleCameraCapture = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.capture = 'environment';
    input.onchange = (e) => {
      const target = e.target as HTMLInputElement;
      if (target.files && target.files[0]) {
        handleProcessFile(target.files[0]);
      }
    };
    input.click();
  };

  const handleRunInference = async () => {
    if (!file) return;

    setAnalyzing(true);
    try {
      const location = shareToRadar ? await getCurrentPosition() : null;
      const res = await apiPredict(file, crop, location);
      setResult(res);
      if (followup.treatment) await followup.submit(res.id);
      showToast(
        'success',
        res.detections.length > 0
          ? `Hoàn tất phân tích: Đã phát hiện ${res.detections.length} vùng tổn thương.`
          : 'Hoàn tất phân tích: Không phát hiện dấu hiệu bệnh hại.'
      );
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Quá trình thực thi chẩn đoán thất bại.';
      showToast('error', msg);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-8 sm:space-y-10">
      {/* Page Title & Context Header */}
      <div className="space-y-1.5">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#F0FDF4] border border-emerald-200/80 text-xs font-bold text-[#15803D]">
          <Leaf size={13} className="text-[#15803D]" />
          <span>Trung Tâm Chẩn Đoán Bệnh Lá Cây Trồng</span>
        </div>
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[#0F172A] tracking-tight font-['Space_Grotesk']">
          Chẩn Đoán Bệnh Lá & <span className="text-gradient">Thị Giác AI</span>
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 max-w-2xl leading-relaxed">
          Chọn loại cây, rồi tải lên hoặc chụp ảnh lá độ nét cao để AI khoanh vùng tổn thương và nhận diện bệnh hại.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Upload & Inspection Workspace (7 cols) */}
        <div className="lg:col-span-7 space-y-6">
          {followup.treatment && (
            <div className="clean-card p-4 rounded-3xl flex items-center gap-4 border-2 border-amber-300 bg-amber-50/60">
              {followup.treatment.original_image_url && (
                <img
                  src={resolveMediaUrl(followup.treatment.original_image_url)}
                  alt="Ảnh lá trước khi điều trị"
                  className="w-20 h-20 rounded-2xl object-cover border border-amber-200 shrink-0"
                />
              )}
              <div className="text-xs text-slate-700 space-y-1">
                <p className="font-bold text-amber-900 text-sm">Chụp lại lá để đánh giá hiệu quả thuốc</p>
                <p>
                  Đã phun <b>{followup.treatment.active_name}</b> ngày {formatDate(followup.treatment.applied_on)}. Hãy chụp
                  <b> cùng chiếc lá</b> (hoặc cùng vị trí), cùng khoảng cách và đủ sáng như ảnh bên cạnh.
                </p>
              </div>
            </div>
          )}

          {!result && !followup.treatment && (
            <CropSelector
              crops={crops}
              value={crop}
              onChange={handleSelectCrop}
              disabled={analyzing}
            />
          )}

          {!previewUrl ? (
            /* Upload Dropzone Card */
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
              className={`clean-card p-10 sm:p-14 lg:p-16 text-center cursor-pointer border-2 border-dashed rounded-3xl transition-all duration-200 flex flex-col items-center justify-center min-h-[420px] ${
                isDragOver
                  ? 'border-emerald-500 bg-[#F0FDF4] shadow-md scale-[1.01]'
                  : 'border-emerald-200 hover:border-emerald-400 bg-white/80 hover:bg-white/95'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleInputChange}
                className="hidden"
              />

              <div className="w-16 h-16 rounded-2xl bg-[#F0FDF4] border border-emerald-200 flex items-center justify-center text-[#15803D] mb-4 shadow-2xs">
                <Upload size={28} />
              </div>

              <h3 className="text-lg sm:text-xl font-bold text-slate-900 font-['Space_Grotesk']">
                Kéo & thả ảnh {leafLabel} vào đây
              </h3>
              <p className="text-xs text-slate-500 max-w-md mt-1.5 mb-6 leading-relaxed">
                Cung cấp hình ảnh bề mặt {leafLabel} rõ nét, đủ ánh sáng ở định dạng JPEG, PNG hoặc WEBP. Dung lượng tối đa {MAX_UPLOAD_MB}MB.
              </p>

              <div className="flex flex-wrap items-center justify-center gap-3">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    fileInputRef.current?.click();
                  }}
                  className="btn-primary text-xs py-2.5 px-5"
                >
                  <Upload size={15} />
                  <span>Chọn Tệp Hình Ảnh</span>
                </button>

                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCameraCapture();
                  }}
                  className="btn-secondary text-xs py-2.5 px-5"
                >
                  <Camera size={15} />
                  <span>Chụp Bằng Máy Ảnh</span>
                </button>
              </div>
            </div>
          ) : result ? (
            /* Completed Result with Bounding Boxes */
            <div className="space-y-4">
              <div className="flex items-center justify-between px-1">
                <span className="text-xs font-bold text-[#15803D] uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles size={14} className="text-amber-500" />
                  Đã Tạo Kết Quả Phân Tích YOLO
                </span>
                <button
                  type="button"
                  onClick={handleClear}
                  className="btn-secondary text-xs py-1.5 px-3.5"
                >
                  <RefreshCw size={13} />
                  <span>Quét Mẫu Lá Khác</span>
                </button>
              </div>

              <BoundingBoxViewer
                originalUrl={result.original_image_url}
                annotatedUrl={result.result_image_url}
                detections={result.detections}
                inferenceTime={result.inference_time}
                status={result.status}
              />
            </div>
          ) : (
            /* Selected File Preview with Diagnosis Action */
            <div className="clean-card p-6 sm:p-7 rounded-3xl space-y-5">
              <div className="relative rounded-2xl overflow-hidden bg-[#0B1319] max-h-[500px] flex items-center justify-center p-4">
                <img
                  src={previewUrl}
                  alt="Xem trước ảnh tải lên"
                  className="max-h-[460px] w-auto max-w-full object-contain rounded-xl shadow-lg"
                />
                <button
                  type="button"
                  onClick={handleClear}
                  className="absolute top-3 right-3 p-2 rounded-full bg-white/90 hover:bg-white text-slate-700 hover:text-red-600 shadow-md transition-colors cursor-pointer"
                  title="Gỡ bỏ ảnh"
                  aria-label="Gỡ bỏ ảnh"
                >
                  <X size={16} />
                </button>
              </div>

              <label className="flex items-start gap-2.5 p-3 rounded-2xl bg-[#F0FDF4] border border-emerald-200 text-xs text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={shareToRadar}
                  onChange={(e) => {
                    setShareToRadar(e.target.checked);
                    storeRadarConsent(e.target.checked);
                  }}
                  className="mt-0.5 accent-[#15803D]"
                />
                <span>
                  <b>Chia sẻ vị trí ẩn danh cho Radar dịch bệnh</b> — giúp cảnh báo sớm cho các vườn xung quanh. Vị trí được làm tròn
                  ~110 m, không hiển thị tên hay tài khoản của bạn. Có thể tắt bất cứ lúc nào.
                </span>
              </label>

              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-1">
                <div className="text-xs text-slate-500 font-medium font-mono">
                  Tệp: <span className="font-bold text-slate-800">{file?.name}</span>{' '}
                  ({file ? (file.size / (1024 * 1024)).toFixed(2) : '0'} MB)
                </div>

                <div className="flex items-center gap-2.5">
                  <button
                    type="button"
                    onClick={handleClear}
                    className="btn-secondary text-xs py-2 px-3.5"
                  >
                    Hủy Bỏ
                  </button>
                  <button
                    type="button"
                    onClick={handleRunInference}
                    disabled={analyzing}
                    className="btn-primary text-xs py-2.5 px-5"
                  >
                    {analyzing ? (
                      <>
                        <Loader2 size={15} className="animate-spin" />
                        <span>Đang chạy mô hình thị giác YOLO...</span>
                      </>
                    ) : (
                      <>
                        <Scan size={15} />
                        <span>Chẩn Đoán Bệnh Lá {cropName(crop)}</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Analysis Summary & Action Plan (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Analysis Results Card */}
          <div className="clean-card p-6 sm:p-7 rounded-3xl space-y-5 shadow-xs">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2 font-['DM_Sans']">
              <Layers size={15} className="text-[#15803D]" />
              Kết Quả Phân Tích
            </h3>

            {result ? (
              <div className="space-y-4 text-xs">
                <div className="p-4 rounded-2xl bg-white/60 border border-[#E2EFE7] space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">Trạng Thái Chẩn Đoán</span>
                    <span
                      className={`font-bold px-2.5 py-0.5 rounded-full text-xs font-mono ${
                        result.status === 'detected'
                          ? 'bg-amber-50 text-amber-800 border border-amber-200'
                          : 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                      }`}
                    >
                      {result.status === 'detected' ? 'Đã Nhận Diện Bệnh Hại' : 'Lá Khỏe Mạnh / Không Có Bệnh'}
                    </span>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-slate-500 font-medium">Tổng Số Vị Trí Tổn Thương</span>
                    <span className="font-extrabold text-slate-900 font-mono text-sm">
                      {result.detections.length}
                    </span>
                  </div>

                  {result.detections.length > 0 && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500 font-medium">Độ Tin Cậy Cao Nhất</span>
                      <span className="font-bold text-[#15803D] font-mono text-sm">
                        {(Math.max(...result.detections.map((d) => d.confidence)) * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}

                  {result.severity_pct != null && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500 font-medium">Diện Tích Vết Bệnh / Lá</span>
                      <span className="font-bold text-slate-900 font-mono text-sm">{formatNumber(result.severity_pct)}%</span>
                    </div>
                  )}

                  {result.inference_time !== null && (
                    <div className="flex items-center justify-between">
                      <span className="text-slate-500 font-medium">Thời Gian Suy Luận</span>
                      <span className="font-mono text-slate-700">
                        {(result.inference_time * 1000).toFixed(0)} ms
                      </span>
                    </div>
                  )}
                </div>

                <div className="space-y-1.5">
                  <span className="font-bold text-slate-900">Tóm Tắt Chẩn Đoán</span>
                  <p className="text-slate-600 leading-relaxed p-3.5 rounded-xl bg-[#F0FDF4] border border-emerald-100 text-xs">
                    {result.summary}
                  </p>
                </div>

                <DiagnosisFeedback
                  key={result.id}
                  diagnosisId={result.id}
                  initial={result.user_feedback}
                />

                {followup.result && <FollowupVerdictCard result={followup.result} />}

                {!followup.treatment && result.status === 'detected' && (
                  <button type="button" onClick={() => setRecordOpen(true)} className="btn-primary text-xs py-2.5 px-4 w-full">
                    <SprayCan size={15} />
                    <span>Ghi nhận đã phun thuốc &amp; nhắc chụp lại sau 3–5 ngày</span>
                  </button>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-400 leading-relaxed py-6 text-center">
                Chọn loại cây, tải ảnh {leafLabel} và bấm "Chẩn Đoán Bệnh Lá {cropName(crop)}" để chạy mô hình AI.
              </p>
            )}
          </div>

          {/* Action Plan & Care Recommendations Card */}
          <div className="clean-card p-6 sm:p-7 rounded-3xl space-y-4 shadow-xs">
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#15803D] flex items-center gap-2 font-['DM_Sans']">
              <Sparkles size={15} className="text-amber-500" />
              Phác Đồ & Biện Pháp Chăm Sóc Nông Học
            </h3>

            {result && result.detections.length > 0 ? (
              <div className="space-y-3 text-xs">
                <div className="p-4 rounded-xl bg-[#F0FDF4] border border-emerald-200/80 space-y-1.5">
                  <span className="font-bold text-[#14532D] flex items-center gap-1.5">
                    <ShieldCheck size={15} className="text-[#15803D]" />
                    Biện Pháp Bảo Vệ Mục Tiêu
                  </span>
                  <p className="text-slate-600 leading-relaxed text-xs">
                    Cách ly, cắt bỏ phần lá bệnh và áp dụng phác đồ đặc trị cho cây {cropName(result.crop_code).toLowerCase()} để ngăn tổn thương lan rộng.{' '}
                    <Link to="/diseases" className="font-bold text-[#15803D] underline underline-offset-2">
                      Xem phác đồ chi tiết trong Thư viện bệnh
                    </Link>
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 space-y-1.5">
                  <span className="font-bold text-amber-900 flex items-center gap-1.5">
                    <Droplets size={15} className="text-amber-600" />
                    Quản Lý Độ Ẩm & Độ Thông Thoáng Tán Cây
                  </span>
                  <p className="text-slate-600 leading-relaxed text-xs">
                    Tỉa bớt cành che bóng để đón ánh nắng, khơi thông rãnh thoát nước để giảm độ ẩm trong tán — phần lớn bệnh lá do nấm bùng phát khi ẩm độ cao.
                  </p>
                </div>
              </div>
            ) : (
              <p className="text-xs text-slate-400 leading-relaxed py-6 text-center">
                Các biện pháp chăm sóc nông học, vệ sinh vườn IPM và khuyến nghị cụ thể sẽ xuất hiện tại đây sau khi triệu chứng được phân tích.
              </p>
            )}
          </div>
        </div>
      </div>

      {result && (
        <RecordTreatmentModal
          open={recordOpen}
          diagnosisId={result.id}
          cropCode={result.crop_code}
          diseaseName={
            result.detections.length > 0
              ? result.detections.reduce((a, b) => (b.confidence > a.confidence ? b : a)).class_name
              : null
          }
          onClose={() => setRecordOpen(false)}
        />
      )}
    </div>
  );
}

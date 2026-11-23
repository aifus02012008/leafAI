import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Loader2, RefreshCw, ScanLine } from 'lucide-react';
import { apiPredict } from '../api/diagnosis';
import { BoundingBoxViewer } from '../components/BoundingBoxViewer';
import { CropSelector } from '../components/CropSelector';
import { FollowupVerdictCard } from '../components/FollowupVerdictCard';
import { RecordTreatmentModal } from '../components/RecordTreatmentModal';
import { Viewfinder } from '../components/diagnose/Viewfinder';
import { PhotoTips } from '../components/diagnose/PhotoTips';
import { DiagnosisVerdict } from '../components/diagnose/DiagnosisVerdict';
import { resolveMediaUrl } from '../api/client';
import { useFollowupTreatment } from '../hooks/useFollowupTreatment';
import { getCurrentPosition, readRadarConsent, storeRadarConsent } from '../hooks/useGeolocation';
import { formatDate } from '../utils/format';
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

function errorDetail(err: unknown): string {
  const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === 'string' ? detail : 'Chưa chẩn đoán được ảnh này. Kiểm tra mạng rồi thử lại.';
}

export function DiagnosePage() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [result, setResult] = useState<DiagnosisResult | null>(null);
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

  // If the remembered crop is no longer available (or unknown), fall back to tea.
  useEffect(() => {
    if (cropsLoading) return;
    const current = crops.find((c) => c.code === crop);
    if (!current || !current.is_available) setCrop(DEFAULT_CROP);
  }, [crops, cropsLoading, crop]);

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  const cropLabel = cropName(crop).toLowerCase();
  const leafLabel = `lá ${cropLabel}`;

  const handleSelectCrop = (code: CropCode) => {
    setCrop(code);
    storeCrop(code);
    setResult(null);
  };

  const handleFile = (selected: File) => {
    if (!selected.type.startsWith('image/')) {
      showToast('error', 'Tệp này không phải ảnh. Hãy chọn ảnh JPEG, PNG hoặc WEBP.');
      return;
    }
    if (selected.size > MAX_UPLOAD_MB * 1024 * 1024) {
      showToast('error', `Ảnh lớn hơn ${MAX_UPLOAD_MB} MB. Hãy chụp lại hoặc chọn ảnh nhỏ hơn.`);
      return;
    }
    setFile(selected);
    setPreviewUrl(URL.createObjectURL(selected));
    setResult(null);
  };

  const handleClear = () => {
    setFile(null);
    setPreviewUrl(null);
    setResult(null);
    followup.reset();
  };

  const handleDiagnose = async () => {
    if (!file) return;
    setAnalyzing(true);
    try {
      const location = shareToRadar ? await getCurrentPosition() : null;
      const res = await apiPredict(file, crop, location);
      setResult(res);
      if (followup.treatment) await followup.submit(res.id);
      showToast(
        'success',
        res.detections.length > 0 ? `${res.detections.length} vùng bệnh` : 'Lá khoẻ'
      );
    } catch (err: unknown) {
      showToast('error', errorDetail(err));
    } finally {
      setAnalyzing(false);
    }
  };

  const topDiseaseName =
    result && result.detections.length > 0
      ? result.detections.reduce((a, b) => (b.confidence > a.confidence ? b : a)).class_name
      : null;

  return (
    <div className="space-y-7">
      {followup.treatment && (
        <div className="rounded-[18px] bg-sun-wash border border-sun p-4 flex items-center gap-4">
          {followup.treatment.original_image_url && (
            <img
              src={resolveMediaUrl(followup.treatment.original_image_url)}
              alt="Ảnh lá trước khi phun thuốc"
              className="w-20 h-20 rounded-xl object-cover shrink-0"
            />
          )}
          <div className="text-sm text-ink/80">
            <p className="font-bold text-ink">Chụp lại đúng lá này</p>
            <p>
              {followup.treatment.active_name} · {formatDate(followup.treatment.applied_on)}
            </p>
          </div>
        </div>
      )}

      {!result && !followup.treatment && (
        <CropSelector crops={crops} value={crop} onChange={handleSelectCrop} disabled={analyzing} />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <section className="lg:col-span-7 space-y-4" aria-label="Ảnh lá">
          {result ? (
            <>
              <BoundingBoxViewer
                originalUrl={result.original_image_url}
                annotatedUrl={result.result_image_url}
                detections={result.detections}
                inferenceTime={result.inference_time}
                status={result.status}
              />
              <button type="button" onClick={handleClear} className="btn-secondary text-sm w-full sm:w-auto">
                <RefreshCw size={15} />
                Chụp lại
              </button>
            </>
          ) : (
            <Viewfinder
              leafLabel={leafLabel}
              maxUploadMb={MAX_UPLOAD_MB}
              previewUrl={previewUrl}
              scanning={analyzing}
              onFile={handleFile}
              onClear={handleClear}
            >
              {previewUrl && (
                <div className="relative border-t border-white/10 p-4 sm:p-5 space-y-4">
                  <label className="flex items-start gap-3 text-[13px] text-white/70 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={shareToRadar}
                      onChange={(e) => {
                        setShareToRadar(e.target.checked);
                        storeRadarConsent(e.target.checked);
                      }}
                      className="mt-0.5 w-4 h-4 accent-[#5EE6A0]"
                    />
                    <span title="Vị trí làm tròn ~110 m, không kèm tên hay tài khoản">Góp vị trí ẩn danh cho Radar</span>
                  </label>
                  <button
                    type="button"
                    onClick={handleDiagnose}
                    disabled={analyzing}
                    className="w-full h-13 inline-flex items-center justify-center gap-2 rounded-xl bg-mint text-forest font-bold text-base hover:bg-[#7BEDB3] disabled:opacity-70 disabled:cursor-wait transition-colors cursor-pointer"
                  >
                    {analyzing ? (
                      <>
                        <Loader2 size={18} className="animate-spin" />
                        Đang phân tích…
                      </>
                    ) : (
                      <>
                        <ScanLine size={18} />
                        Chẩn đoán
                      </>
                    )}
                  </button>
                </div>
              )}
            </Viewfinder>
          )}
        </section>

        <aside className="lg:col-span-5" aria-label="Kết quả chẩn đoán">
          {result ? (
            <DiagnosisVerdict
              result={result}
              canRecordTreatment={!followup.treatment && result.status === 'detected'}
              onRecordTreatment={() => setRecordOpen(true)}
              followupSlot={followup.result ? <FollowupVerdictCard result={followup.result} /> : undefined}
            />
          ) : (
            <PhotoTips />
          )}
        </aside>
      </div>

      {result && (
        <RecordTreatmentModal
          open={recordOpen}
          diagnosisId={result.id}
          cropCode={result.crop_code}
          diseaseName={topDiseaseName}
          onClose={() => setRecordOpen(false)}
        />
      )}
    </div>
  );
}

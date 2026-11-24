import { useCallback, useEffect, useRef, useState } from 'react';
import { AlertTriangle, BellPlus, CloudRain, Loader2, LocateFixed, Radar } from 'lucide-react';
import { apiGetRadar } from '../api/radar';
import { apiCreateFarm } from '../api/farms';
import { RadarMap } from '../components/RadarMap';
import { WeatherForecast } from '../components/radar/WeatherForecast';
import { showToast } from '../components/Toast';
import { useCrops } from '../hooks/useCrops';
import { getCurrentPosition } from '../hooks/useGeolocation';
import type { CropCode, GeoPoint, RadarResponse, RiskLevel } from '../types';

/** Sample growing areas so the radar can be explored without sharing a location. */
const PRESET_AREAS: { label: string; point: GeoPoint }[] = [
  { label: 'Cái Mơn, Bến Tre (sầu riêng)', point: { lat: 10.2401, lng: 106.3756 } },
  { label: 'Lục Ngạn, Bắc Giang (vải thiều)', point: { lat: 21.3833, lng: 106.65 } },
  { label: 'Tân Cương, Thái Nguyên (chè)', point: { lat: 21.5594, lng: 105.7708 } },
  { label: 'Krông Pắc, Đắk Lắk (sầu riêng)', point: { lat: 12.6944, lng: 108.3253 } },
  { label: 'Bình Minh, Vĩnh Long (bưởi Năm Roi)', point: { lat: 10.0369, lng: 105.8217 } },
];

const LEVEL_META: Record<RiskLevel, { label: string; className: string }> = {
  high: { label: 'Nguy cơ cao', className: 'bg-red-50 border-red-300 text-red-800' },
  medium: { label: 'Nguy cơ trung bình', className: 'bg-amber-50 border-amber-300 text-amber-900' },
  low: { label: 'Nguy cơ thấp', className: 'bg-emerald-50 border-emerald-200 text-emerald-900' },
};


export function RadarPage() {
  const { crops, cropName } = useCrops();
  const [point, setPoint] = useState<GeoPoint>(PRESET_AREAS[0].point);
  const [areaLabel, setAreaLabel] = useState(PRESET_AREAS[0].label);
  const [crop, setCrop] = useState<CropCode | ''>('');
  const [radius, setRadius] = useState(5);
  const [data, setData] = useState<RadarResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [locating, setLocating] = useState(false);

  const requestSeq = useRef(0);

  const load = useCallback(async (p: GeoPoint, r: number, c: CropCode | '') => {
    const seq = ++requestSeq.current; // ignore responses from superseded filter changes
    setLoading(true);
    try {
      const res = await apiGetRadar(p, r, c || null);
      if (seq === requestSeq.current) setData(res);
    } catch {
      if (seq === requestSeq.current) showToast('error', 'Không tải được dữ liệu radar dịch bệnh.');
    } finally {
      if (seq === requestSeq.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load(point, radius, crop);
  }, [load, point, radius, crop]);

  const [watching, setWatching] = useState(false);

  const watchArea = async () => {
    setWatching(true);
    try {
      await apiCreateFarm({
        name: areaLabel.slice(0, 100),
        latitude: point.lat,
        longitude: point.lng,
        radius_km: radius,
        crop_code: crop || null,
      });
      showToast('success', 'Đã theo dõi vùng này. Cảnh báo sẽ hiện ở chuông và mục "Vườn".');
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      showToast('error', typeof detail === 'string' ? detail : 'Không theo dõi được vùng này.');
    } finally {
      setWatching(false);
    }
  };

  const useMyLocation = async () => {
    setLocating(true);
    const pos = await getCurrentPosition();
    setLocating(false);
    if (!pos) {
      showToast('error', 'Không lấy được vị trí. Hãy cho phép quyền vị trí hoặc chọn vùng có sẵn.');
      return;
    }
    setPoint(pos);
    setAreaLabel('Vị trí hiện tại của bạn');
  };

  return (
    <div className="space-y-6">

      <div className="clean-card p-4 flex flex-col lg:flex-row gap-3 lg:items-end">
        <div className="flex-1 min-w-0">
          <label htmlFor="radar-area" className="block text-[11px] font-bold text-slate-600 mb-1">Khu vực</label>
          <select
            id="radar-area"
            value={PRESET_AREAS.findIndex((a) => a.label === areaLabel)}
            onChange={(e) => {
              const area = PRESET_AREAS[Number(e.target.value)];
              if (area) {
                setPoint(area.point);
                setAreaLabel(area.label);
              }
            }}
            className="input-clean py-2 text-sm"
          >
            {areaLabel === 'Vị trí hiện tại của bạn' && <option value={-1}>Vị trí hiện tại của bạn</option>}
            {PRESET_AREAS.map((a, i) => <option key={a.label} value={i}>{a.label}</option>)}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-3 lg:w-80">
          <div>
            <label htmlFor="radar-crop" className="block text-[11px] font-bold text-slate-600 mb-1">Cây trồng</label>
            <select id="radar-crop" value={crop} onChange={(e) => setCrop(e.target.value)} className="input-clean py-2 text-sm">
              <option value="">Tất cả</option>
              {crops.map((c) => <option key={c.code} value={c.code}>{c.name_vi}</option>)}
            </select>
          </div>
          <div>
            <label htmlFor="radar-radius" className="block text-[11px] font-bold text-slate-600 mb-1">Bán kính</label>
            <select id="radar-radius" value={radius} onChange={(e) => setRadius(Number(e.target.value))} className="input-clean py-2 text-sm">
              {[2, 5, 10, 20].map((r) => <option key={r} value={r}>{r} km</option>)}
            </select>
          </div>
        </div>
        <button type="button" onClick={useMyLocation} disabled={locating} className="btn-secondary text-xs py-2.5 px-4">
          {locating ? <Loader2 size={14} className="animate-spin" /> : <LocateFixed size={14} />}
          <span>Vị trí tôi</span>
        </button>
        <button type="button" onClick={watchArea} disabled={watching} className="btn-primary text-xs py-2.5 px-4">
          {watching ? <Loader2 size={14} className="animate-spin" /> : <BellPlus size={14} />}
          <span>Theo dõi</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-7">
          <div className="clean-card p-3 relative">
            <RadarMap center={point} radiusKm={radius} cells={data?.grid ?? []} />
            {loading && (
              <div className="absolute inset-0 flex items-center justify-center bg-white/50 rounded-3xl z-10">
                <Loader2 size={24} className="animate-spin text-[#1F7A4D]" />
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-5 space-y-4">
          <section aria-labelledby="radar-weather" className="clean-card p-4 space-y-3">
            <h2 id="radar-weather" className="text-xs font-bold uppercase tracking-wider text-[#1F7A4D] flex items-center gap-2">
              <CloudRain size={15} /> 7 ngày tới
            </h2>
            <WeatherForecast days={data?.weather} recentRainMm={data?.recent_rain_mm} sprayWindows={data?.spray_windows} />
          </section>

          <section aria-labelledby="radar-alerts" className="clean-card p-4 space-y-3">
            <h2 id="radar-alerts" className="text-xs font-bold uppercase tracking-wider text-[#1F7A4D] flex items-center gap-2">
              <Radar size={15} /> Cảnh báo
            </h2>
            {data && data.alerts.length === 0 && (
              <p className="text-xs text-slate-600">Chưa có ca bệnh trong {radius} km</p>
            )}
            <ul className="space-y-2.5">
              {data?.alerts.map((a) => (
                <li key={`${a.crop_code}-${a.disease}`} className={`p-3.5 rounded-2xl border text-xs space-y-1.5 ${LEVEL_META[a.level].className}`}>
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-bold flex items-center gap-1.5">
                      <AlertTriangle size={13} /> {LEVEL_META[a.level].label}
                    </span>
                    <span className="font-semibold">{cropName(a.crop_code)} · {a.cases} ca</span>
                  </div>
                  <p className="leading-relaxed text-slate-800">{a.message}</p>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}

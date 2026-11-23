import { useEffect, useState, type FormEvent } from 'react';
import { BellRing, Loader2, LocateFixed, MapPin, Plus, ShieldCheck, Trash2 } from 'lucide-react';
import { apiCreateFarm, apiDeleteFarm, apiListFarms, apiPurgeLocation, apiUpdateFarm } from '../api/farms';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { showToast } from '../components/Toast';
import { useCrops } from '../hooks/useCrops';
import { getCurrentPosition } from '../hooks/useGeolocation';
import { usePushNotifications, type PushState } from '../hooks/usePushNotifications';
import type { CropCode, WatchedFarm } from '../types';

const PUSH_TEXT: Record<PushState, string> = {
  loading: 'Đang kiểm tra…',
  unsupported: 'Trình duyệt này chưa hỗ trợ thông báo đẩy. Trên iPhone, hãy thêm LEAF_AI ra màn hình chính trước.',
  'server-disabled': 'Máy chủ chưa bật thông báo đẩy. Cảnh báo vẫn hiện ở biểu tượng chuông.',
  denied: 'Bạn đã chặn thông báo. Hãy cho phép lại trong phần cài đặt trang web của trình duyệt.',
  off: 'Chưa bật thông báo trên thiết bị này.',
  on: 'Đã bật thông báo trên thiết bị này.',
};

function errorText(err: any, fallback: string): string {
  const detail = err?.response?.data?.detail;
  return typeof detail === 'string' ? detail : fallback;
}

function AddFarmForm({ onAdded }: { onAdded: (f: WatchedFarm) => void }) {
  const { crops } = useCrops();
  const [name, setName] = useState('');
  const [crop, setCrop] = useState<CropCode | ''>('');
  const [radius, setRadius] = useState(5);
  const [point, setPoint] = useState<{ lat: number; lng: number } | null>(null);
  const [locating, setLocating] = useState(false);
  const [saving, setSaving] = useState(false);

  const locate = async () => {
    setLocating(true);
    const pos = await getCurrentPosition();
    setLocating(false);
    if (!pos) showToast('error', 'Không lấy được vị trí. Hãy cho phép quyền vị trí cho trang web.');
    else setPoint(pos);
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !point) {
      showToast('error', 'Nhập tên vườn và lấy vị trí vườn trước khi lưu.');
      return;
    }
    setSaving(true);
    try {
      const farm = await apiCreateFarm({ name: name.trim(), latitude: point.lat, longitude: point.lng, radius_km: radius, crop_code: crop || null });
      onAdded(farm);
      setName('');
      setPoint(null);
      showToast('success', 'Đã thêm vườn. LEAF AI sẽ cảnh báo khi quanh vườn có nguy cơ dịch bệnh cao.');
    } catch (err) {
      showToast('error', errorText(err, 'Không lưu được vườn.'));
    } finally {
      setSaving(false);
    }
  };

  const label = 'block text-[11px] font-bold text-slate-600 mb-1';
  return (
    <form onSubmit={submit} className="clean-card p-5 rounded-3xl space-y-3">
      <h2 className="text-xs font-bold uppercase tracking-wider text-[#15803D] flex items-center gap-2">
        <Plus size={15} /> Thêm vườn cần theo dõi
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
        <div className="sm:col-span-1">
          <label htmlFor="farm-name" className={label}>Tên vườn</label>
          <input id="farm-name" maxLength={100} value={name} onChange={(e) => setName(e.target.value)} placeholder="vd: Vườn sau nhà" className="input-clean py-2 text-sm" />
        </div>
        <div>
          <label htmlFor="farm-crop" className={label}>Cây trồng</label>
          <select id="farm-crop" value={crop} onChange={(e) => setCrop(e.target.value)} className="input-clean py-2 text-sm">
            <option value="">Mọi loại cây</option>
            {crops.map((c) => <option key={c.code} value={c.code}>{c.name_vi}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="farm-radius" className={label}>Bán kính cảnh báo</label>
          <select id="farm-radius" value={radius} onChange={(e) => setRadius(Number(e.target.value))} className="input-clean py-2 text-sm">
            {[2, 5, 10, 20].map((r) => <option key={r} value={r}>{r} km</option>)}
          </select>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2.5">
        <button type="button" onClick={locate} disabled={locating} className="btn-secondary text-xs py-2 px-3.5">
          {locating ? <Loader2 size={14} className="animate-spin" /> : <LocateFixed size={14} />}
          <span>{point ? 'Lấy lại vị trí' : 'Dùng vị trí hiện tại'}</span>
        </button>
        {point && (
          <span className="text-xs text-slate-600 inline-flex items-center gap-1">
            <MapPin size={13} className="text-[#15803D]" /> {point.lat.toFixed(3)}, {point.lng.toFixed(3)}
          </span>
        )}
        <button type="submit" disabled={saving} className="btn-primary text-xs py-2.5 px-4 ml-auto">
          {saving ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
          <span>Lưu vườn</span>
        </button>
      </div>
      <p className="text-[11px] text-slate-500">Đứng tại vườn rồi bấm "Dùng vị trí hiện tại". Vị trí được làm tròn khoảng 110 m.</p>
    </form>
  );
}

export function FarmsPage() {
  const { cropName } = useCrops();
  const push = usePushNotifications();
  const [farms, setFarms] = useState<WatchedFarm[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [purgeOpen, setPurgeOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    apiListFarms()
      .then((data) => active && setFarms(data))
      .catch(() => showToast('error', 'Không tải được danh sách vườn.'))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  const toggleAlerts = async (farm: WatchedFarm) => {
    try {
      const updated = await apiUpdateFarm(farm.id, { alerts_enabled: !farm.alerts_enabled });
      setFarms((prev) => prev.map((f) => (f.id === farm.id ? updated : f)));
    } catch (err) {
      showToast('error', errorText(err, 'Không cập nhật được vườn.'));
    }
  };

  const confirmDelete = async () => {
    if (deleteId === null) return;
    setBusy(true);
    try {
      await apiDeleteFarm(deleteId);
      setFarms((prev) => prev.filter((f) => f.id !== deleteId));
      setDeleteId(null);
    } catch (err) {
      showToast('error', errorText(err, 'Xóa vườn thất bại.'));
    } finally {
      setBusy(false);
    }
  };

  const confirmPurge = async () => {
    setBusy(true);
    try {
      const res = await apiPurgeLocation();
      setFarms([]);
      setPurgeOpen(false);
      showToast('success', `Đã xóa vị trí của ${res.diagnoses_cleared} lần chẩn đoán và ${res.farms_deleted} vườn.`);
    } catch (err) {
      showToast('error', errorText(err, 'Không xóa được dữ liệu vị trí.'));
    } finally {
      setBusy(false);
    }
  };

  const togglePush = async () => {
    try {
      if (push.state === 'on') await push.disable();
      else await push.enable();
    } catch {
      showToast('error', 'Không bật được thông báo trên thiết bị này.');
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      <div className="space-y-1.5">
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-[#0F172A] tracking-tight font-['Space_Grotesk']">
          Vườn & <span className="text-gradient">Thông Báo</span>
        </h1>
        <p className="text-xs sm:text-sm text-slate-500">
          Lưu vị trí vườn để nhận cảnh báo khi quanh vườn có nhiều ca bệnh và thời tiết thuận lợi cho bệnh lây lan.
        </p>
      </div>

      <section className="clean-card p-5 rounded-3xl flex flex-col sm:flex-row sm:items-center gap-3 justify-between" aria-labelledby="push-title">
        <div className="space-y-1">
          <h2 id="push-title" className="text-xs font-bold uppercase tracking-wider text-[#15803D] flex items-center gap-2">
            <BellRing size={15} /> Thông báo trên điện thoại
          </h2>
          <p className="text-xs text-slate-600">{PUSH_TEXT[push.state]}</p>
        </div>
        {(push.state === 'on' || push.state === 'off') && (
          <button type="button" onClick={togglePush} disabled={push.busy} className={push.state === 'on' ? 'btn-secondary text-xs py-2 px-4' : 'btn-primary text-xs py-2 px-4'}>
            {push.busy && <Loader2 size={14} className="animate-spin" />}
            <span>{push.state === 'on' ? 'Tắt thông báo' : 'Bật thông báo'}</span>
          </button>
        )}
      </section>

      <AddFarmForm onAdded={(f) => setFarms((prev) => [...prev, f])} />

      <section aria-labelledby="farms-title" className="space-y-3">
        <h2 id="farms-title" className="text-xs font-bold uppercase tracking-wider text-slate-500">Vườn đang theo dõi</h2>
        {loading ? (
          <p className="text-xs text-slate-500">Đang tải…</p>
        ) : farms.length === 0 ? (
          <p className="text-xs text-slate-500">Chưa có vườn nào.</p>
        ) : (
          <ul className="space-y-2.5">
            {farms.map((f) => (
              <li key={f.id} className="clean-card p-4 rounded-2xl flex flex-col sm:flex-row sm:items-center gap-3">
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-bold text-slate-900 truncate">{f.name}</p>
                  <p className="text-xs text-slate-500">
                    {f.crop_code ? cropName(f.crop_code) : 'Mọi loại cây'} · bán kính {f.radius_km} km · {f.latitude.toFixed(3)}, {f.longitude.toFixed(3)}
                  </p>
                </div>
                <label className="inline-flex items-center gap-2 text-xs font-semibold text-slate-700 cursor-pointer">
                  <input type="checkbox" checked={f.alerts_enabled} onChange={() => toggleAlerts(f)} className="accent-[#15803D]" />
                  Nhận cảnh báo
                </label>
                <button type="button" onClick={() => setDeleteId(f.id)} aria-label={`Xóa vườn ${f.name}`} className="p-2 rounded-xl border border-red-200 text-red-600 hover:bg-red-50 self-end sm:self-auto">
                  <Trash2 size={14} />
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="clean-card p-5 rounded-3xl space-y-2" aria-labelledby="privacy-title">
        <h2 id="privacy-title" className="text-xs font-bold uppercase tracking-wider text-[#15803D] flex items-center gap-2">
          <ShieldCheck size={15} /> Quyền riêng tư
        </h2>
        <p className="text-xs text-slate-600">
          Xóa toàn bộ vị trí bạn đã chia sẻ cho Radar dịch bệnh và các vườn đang theo dõi. Kết quả chẩn đoán vẫn được giữ, chỉ bỏ thông tin vị trí.
        </p>
        <button type="button" onClick={() => setPurgeOpen(true)} className="btn-secondary text-xs py-2 px-4 text-red-700">
          <Trash2 size={14} /> <span>Xóa dữ liệu vị trí của tôi</span>
        </button>
      </section>

      <ConfirmDialog
        open={deleteId !== null}
        title="Xóa vườn?"
        message="Bạn sẽ không nhận cảnh báo dịch bệnh cho vườn này nữa."
        loading={busy}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteId(null)}
      />
      <ConfirmDialog
        open={purgeOpen}
        title="Xóa toàn bộ dữ liệu vị trí?"
        message="Vị trí của mọi lần chẩn đoán đã chia sẻ và tất cả vườn theo dõi sẽ bị xóa vĩnh viễn, không khôi phục được."
        confirmLabel="Xóa vị trí"
        loading={busy}
        onConfirm={confirmPurge}
        onCancel={() => setPurgeOpen(false)}
      />
    </div>
  );
}

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
  unsupported: 'Máy này chưa hỗ trợ',
  'server-disabled': 'Chưa khả dụng',
  denied: 'Đã bị chặn trong trình duyệt',
  off: 'Đang tắt',
  on: 'Đang bật',
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
    <form onSubmit={submit} className="clean-card p-5 space-y-3">
      <h2 className="text-xs font-bold uppercase tracking-wider text-[#1F7A4D] flex items-center gap-2">
        <Plus size={15} /> Thêm vườn
      </h2>
      <div className="grid grid-cols-2 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_6.5rem_auto_auto] gap-3 items-end text-sm">
        <div className="col-span-2 lg:col-span-1">
          <label htmlFor="farm-name" className={label}>Tên vườn</label>
          <input id="farm-name" maxLength={100} value={name} onChange={(e) => setName(e.target.value)} placeholder="Vườn sau nhà" className="input-clean py-2 text-sm" />
        </div>
        <div>
          <label htmlFor="farm-crop" className={label}>Cây trồng</label>
          <select id="farm-crop" value={crop} onChange={(e) => setCrop(e.target.value)} className="input-clean py-2 text-sm">
            <option value="">Mọi cây</option>
            {crops.map((c) => <option key={c.code} value={c.code}>{c.name_vi}</option>)}
          </select>
        </div>
        <div>
          <label htmlFor="farm-radius" className={label}>Bán kính</label>
          <select id="farm-radius" value={radius} onChange={(e) => setRadius(Number(e.target.value))} className="input-clean py-2 text-sm">
            {[2, 5, 10, 20].map((r) => <option key={r} value={r}>{r} km</option>)}
          </select>
        </div>
        <button
          type="button"
          onClick={locate}
          disabled={locating}
          title={point ? `${point.lat.toFixed(3)}, ${point.lng.toFixed(3)}` : undefined}
          className={`btn-secondary text-xs h-[38px] px-3.5 ${point ? 'border-[#1F7A4D] text-[#1F7A4D]' : ''}`}
        >
          {locating ? <Loader2 size={14} className="animate-spin" /> : point ? <MapPin size={14} /> : <LocateFixed size={14} />}
          <span>{point ? 'Đã lấy vị trí' : 'Vị trí tôi'}</span>
        </button>
        <button type="submit" disabled={saving} className="btn-primary text-xs h-[38px] px-4">
          {saving ? <Loader2 size={14} className="animate-spin" /> : <Plus size={14} />}
          <span>Lưu</span>
        </button>
      </div>
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
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
      <div className="lg:col-span-8 space-y-6">
        <AddFarmForm onAdded={(f) => setFarms((prev) => [...prev, f])} />

        <section aria-labelledby="farms-title" className="space-y-3">
          <h2 id="farms-title" className="text-xs font-bold uppercase tracking-wider text-slate-500">Đang theo dõi</h2>
          {loading ? (
            <p className="text-xs text-slate-500">Đang tải…</p>
          ) : farms.length === 0 ? (
            <p className="text-xs text-slate-500">Chưa có vườn</p>
          ) : (
            <ul className="grid grid-cols-1 xl:grid-cols-2 gap-3">
              {farms.map((f) => (
                <li key={f.id} className="clean-card px-4 py-3 flex items-center gap-3">
                  <MapPin size={16} className="text-[#1F7A4D] shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-bold text-slate-900 truncate">{f.name}</p>
                    <p className="text-xs text-slate-500">
                      {f.crop_code ? cropName(f.crop_code) : 'Mọi cây'} · {f.radius_km} km
                    </p>
                  </div>
                  <label className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 cursor-pointer" title="Nhận cảnh báo">
                    <input type="checkbox" checked={f.alerts_enabled} onChange={() => toggleAlerts(f)} className="accent-[#1F7A4D]" />
                    <BellRing size={14} aria-hidden="true" />
                    <span className="sr-only">Cảnh báo</span>
                  </label>
                  <button type="button" onClick={() => setDeleteId(f.id)} aria-label={`Xóa vườn ${f.name}`} className="p-2 rounded-xl text-red-600 hover:bg-red-50">
                    <Trash2 size={14} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <aside className="lg:col-span-4 space-y-6">
        <section className="clean-card p-5 flex items-center gap-3 justify-between" aria-labelledby="push-title">
          <div className="space-y-0.5">
            <h2 id="push-title" className="text-xs font-bold uppercase tracking-wider text-[#1F7A4D] flex items-center gap-2">
              <BellRing size={15} /> Thông báo
            </h2>
            <p className="text-xs text-slate-600">{PUSH_TEXT[push.state]}</p>
          </div>
          {(push.state === 'on' || push.state === 'off') && (
            <button type="button" onClick={togglePush} disabled={push.busy} className={push.state === 'on' ? 'btn-secondary text-xs py-2 px-4' : 'btn-primary text-xs py-2 px-4'}>
              {push.busy && <Loader2 size={14} className="animate-spin" />}
              <span>{push.state === 'on' ? 'Tắt' : 'Bật'}</span>
            </button>
          )}
        </section>

        <section className="clean-card p-5 flex items-center gap-3 justify-between" aria-labelledby="privacy-title">
          <h2 id="privacy-title" className="text-xs font-bold uppercase tracking-wider text-[#1F7A4D] flex items-center gap-2">
            <ShieldCheck size={15} /> Quyền riêng tư
          </h2>
          <button type="button" onClick={() => setPurgeOpen(true)} className="btn-secondary text-xs py-2 px-3.5 text-red-700">
            <Trash2 size={14} /> <span>Xóa vị trí</span>
          </button>
        </section>
      </aside>

      <ConfirmDialog
        open={deleteId !== null}
        title="Xóa vườn?"
        message="Ngừng cảnh báo cho vườn này."
        loading={busy}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteId(null)}
      />
      <ConfirmDialog
        open={purgeOpen}
        title="Xóa toàn bộ dữ liệu vị trí?"
        message="Xóa vĩnh viễn mọi vị trí đã chia sẻ và các vườn. Kết quả chẩn đoán vẫn giữ."
        confirmLabel="Xóa vị trí"
        loading={busy}
        onConfirm={confirmPurge}
        onCancel={() => setPurgeOpen(false)}
      />
    </div>
  );
}

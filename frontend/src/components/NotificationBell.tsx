import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, CheckCheck, Radar, SprayCan } from 'lucide-react';
import { apiListNotifications, apiMarkAllNotificationsRead, apiMarkNotificationRead } from '../api/farms';
import type { AppNotification } from '../types';

const POLL_MS = 60_000;
const PANEL_ID = 'notification-panel';

/** Only same-app paths are followed (blocks //host and backslash open-redirect tricks). */
function isInAppLink(link: string | null): link is string {
  return !!link && link.startsWith('/') && !link.startsWith('//') && !link.includes('\\');
}

function timeAgo(iso: string): string {
  const diff = Math.max(0, Date.now() - new Date(iso.endsWith('Z') ? iso : `${iso}Z`).getTime());
  const min = Math.round(diff / 60_000);
  if (min < 60) return `${Math.max(1, min)} phút trước`;
  const h = Math.round(min / 60);
  if (h < 24) return `${h} giờ trước`;
  return `${Math.round(h / 24)} ngày trước`;
}

/** Header bell: unread badge + dropdown of recent alerts. Polls every minute. */
export function NotificationBell() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<AppNotification[]>([]);
  const [unread, setUnread] = useState(0);
  const ref = useRef<HTMLDivElement | null>(null);

  const load = useCallback(() => {
    apiListNotifications()
      .then((res) => {
        setItems(res.items);
        setUnread(res.unread_count);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    load();
    const id = window.setInterval(() => {
      if (document.visibilityState === 'visible') load();
    }, POLL_MS);
    return () => window.clearInterval(id);
  }, [load]);

  useEffect(() => {
    if (!open) return;
    load(); // opening the bell always shows the latest alerts, not the last poll
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('mousedown', onClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onClick);
      document.removeEventListener('keydown', onKey);
    };
  }, [open, load]);

  const openItem = async (n: AppNotification) => {
    if (!n.read_at) {
      await apiMarkNotificationRead(n.id).catch(() => undefined);
      load();
    }
    setOpen(false);
    if (isInAppLink(n.link)) navigate(n.link);
  };

  const readAll = async () => {
    await apiMarkAllNotificationsRead().catch(() => undefined);
    load();
  };

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-label={unread ? `Thông báo, ${unread} chưa đọc` : 'Thông báo'}
        aria-expanded={open}
        aria-controls={PANEL_ID}
        className="relative w-9 h-9 rounded-xl border border-[#DCE5DC] hover:bg-emerald-50 text-slate-600 flex items-center justify-center transition-colors cursor-pointer"
      >
        <Bell size={16} />
        {unread > 0 && (
          <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-full bg-red-600 text-white text-[10px] font-bold flex items-center justify-center">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div
          id={PANEL_ID}
          role="region"
          aria-label="Danh sách thông báo"
          className="absolute right-0 mt-2 w-[min(92vw,360px)] max-h-[70vh] overflow-y-auto bg-white rounded-2xl border border-[#DCE5DC] shadow-xl z-50"
        >
          <div className="flex items-center justify-between px-4 py-3 border-b border-[#DCE5DC] sticky top-0 bg-white">
            <span className="text-sm font-bold text-slate-900">Thông báo</span>
            {unread > 0 && (
              <button type="button" onClick={readAll} className="text-xs font-bold text-[#1F7A4D] inline-flex items-center gap-1">
                <CheckCheck size={13} /> Đánh dấu đã đọc
              </button>
            )}
          </div>
          {items.length === 0 ? (
            <p className="px-4 py-8 text-center text-xs text-slate-500">
              Chưa có thông báo. Thêm vườn ở mục "Vườn" để nhận cảnh báo.
            </p>
          ) : (
            <ul>
              {items.map((n) => (
                <li key={n.id}>
                  <button
                    type="button"
                    onClick={() => openItem(n)}
                    className={`w-full text-left px-4 py-3 flex gap-3 border-b border-slate-100 hover:bg-emerald-50/60 ${n.read_at ? '' : 'bg-amber-50/50'}`}
                  >
                    <span className={`mt-0.5 shrink-0 ${n.kind === 'radar' ? 'text-red-600' : 'text-[#1F7A4D]'}`}>
                      {n.kind === 'radar' ? <Radar size={16} /> : <SprayCan size={16} />}
                    </span>
                    <span className="min-w-0">
                      <span className="block text-xs font-bold text-slate-900">{n.title}</span>
                      <span className="block text-xs text-slate-600 line-clamp-3">{n.body}</span>
                      <span className="block text-[10px] text-slate-400 mt-1">{timeAgo(n.created_at)}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

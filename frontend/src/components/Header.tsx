import { useNavigate, useLocation } from 'react-router-dom';
import { Menu, ScanEye } from 'lucide-react';
import { NotificationBell } from './NotificationBell';

const ROUTE_TITLES: Record<string, string> = {
  '/dashboard': 'Tổng quan',
  '/diagnose': 'Chụp lá',
  '/diseases': 'Thư viện bệnh',
  '/history': 'Lịch sử',
  '/farms': 'Vườn',
  '/radar': 'Radar',
  '/treatments': 'Nhật ký',
  '/tools': 'Tính liều',
  '/assistant': 'Hỏi đáp',
};

interface HeaderProps {
  onToggleMobileSidebar?: () => void;
}

export function Header({ onToggleMobileSidebar }: HeaderProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const title = ROUTE_TITLES[location.pathname] ?? 'LEAF_AI';

  return (
    <header className="w-full h-16 px-4 sm:px-8 bg-paper/90 backdrop-blur-md border-b border-line flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-3 min-w-0">
        {onToggleMobileSidebar && (
          <button
            type="button"
            onClick={onToggleMobileSidebar}
            aria-label="Mở menu"
            className="md:hidden p-2 -ml-2 rounded-xl text-ink hover:bg-black/5 transition-colors cursor-pointer"
          >
            <Menu size={20} />
          </button>
        )}
        <h1 className="font-display font-bold text-lg text-ink truncate">{title}</h1>
      </div>

      <div className="flex items-center gap-2.5">
        {!['/diagnose', '/dashboard'].includes(location.pathname) && (
          <button
            type="button"
            onClick={() => navigate('/diagnose')}
            className="btn-primary text-xs py-2 px-3.5 hidden sm:inline-flex"
          >
            <ScanEye size={15} />
            <span>Chụp lá</span>
          </button>
        )}
        <NotificationBell />
      </div>
    </header>
  );
}

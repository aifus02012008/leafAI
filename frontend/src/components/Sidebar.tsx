import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  ScanEye,
  BookOpen,
  History,
  LogOut,
  SprayCan,
  Calculator,
  Radar,
  BellRing,
  type LucideIcon,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { showToast } from './Toast';

interface NavItem {
  path: string;
  label: string;
  icon: LucideIcon;
  isNew?: boolean;
}

interface NavGroup {
  title: string | null;
  items: readonly NavItem[];
}

/** Grouped by what the farmer is trying to do, in the order they usually do it. */
const NAV_GROUPS: readonly NavGroup[] = [
  {
    title: null,
    items: [{ path: '/dashboard', label: 'Tổng quan', icon: LayoutDashboard }],
  },
  {
    title: 'Chẩn đoán',
    items: [
      { path: '/diagnose', label: 'Chụp lá', icon: ScanEye },
      { path: '/history', label: 'Lịch sử', icon: History },
      { path: '/diseases', label: 'Thư viện bệnh', icon: BookOpen },
    ],
  },
  {
    title: 'Điều trị',
    items: [
      { path: '/treatments', label: 'Nhật ký', icon: SprayCan },
      { path: '/tools', label: 'Tính liều', icon: Calculator },
    ],
  },
  {
    title: 'Cảnh báo',
    items: [
      { path: '/radar', label: 'Radar', icon: Radar, isNew: true },
      { path: '/farms', label: 'Vườn', icon: BellRing },
    ],
  },
];

interface SidebarProps {
  onItemClick?: () => void;
}

function LeafMark() {
  return (
    <svg viewBox="0 0 32 32" className="w-9 h-9" aria-hidden="true">
      <rect width="32" height="32" rx="9" fill="#5EE6A0" />
      <path d="M9 23c0-8 5-13 14-14-1 9-6 14-14 14Z" fill="#0F2A20" />
      <path d="M9.5 22.5 19 13" stroke="#5EE6A0" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

export function Sidebar({ onItemClick }: SidebarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    showToast('info', 'Đã đăng xuất.');
    navigate('/login');
  };

  return (
    <aside className="w-64 h-full bg-forest text-white/80 flex flex-col shrink-0 select-none">
      <button
        type="button"
        onClick={() => {
          navigate('/dashboard');
          onItemClick?.();
        }}
        className="px-5 pt-6 pb-5 flex items-center gap-3 text-left cursor-pointer"
      >
        <LeafMark />
        <span className="font-display font-extrabold text-xl tracking-tight text-white">
          LEAF<span className="text-mint">_AI</span>
        </span>
      </button>

      <nav className="flex-1 overflow-y-auto px-3 pb-4 space-y-5" aria-label="Điều hướng chính">
        {NAV_GROUPS.map((group) => (
          <div key={group.title ?? 'home'} className="space-y-0.5">
            {group.title && (
              <p className="px-3 pb-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-mint/70">
                {group.title}
              </p>
            )}
            {group.items.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={onItemClick}
                  className={({ isActive }) =>
                    `relative flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-colors ${
                      isActive ? 'bg-forest-3 text-white' : 'text-white/70 hover:text-white hover:bg-forest-2'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      {isActive && (
                        <span className="absolute left-0 top-2 bottom-2 w-[3px] rounded-full bg-mint" aria-hidden="true" />
                      )}
                      <Icon size={18} className={isActive ? 'text-mint' : 'text-white/50'} />
                      <span className="flex-1">{item.label}</span>
                      {item.isNew && (
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-sun text-forest">Mới</span>
                      )}
                    </>
                  )}
                </NavLink>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="p-4 space-y-3 border-t border-white/10">
        <div className="flex items-center gap-2.5 rounded-xl bg-forest-2 p-2.5">
          <div className="w-8 h-8 rounded-full bg-mint text-forest flex items-center justify-center font-bold text-xs shrink-0">
            {user?.email?.charAt(0).toUpperCase() || 'U'}
          </div>
          <p className="flex-1 min-w-0 text-xs font-semibold text-white truncate" title={user?.email}>
            {user?.email ? user.email.split('@')[0] : 'Tài khoản'}
          </p>
          <button
            type="button"
            onClick={handleLogout}
            title="Đăng xuất"
            aria-label="Đăng xuất"
            className="w-8 h-8 rounded-lg text-white/50 hover:text-white hover:bg-white/10 flex items-center justify-center transition-colors cursor-pointer"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}

import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import {
  Leaf,
  LayoutDashboard,
  ScanEye,
  BookOpen,
  History,
  LogOut,
  Sparkles,
  ChevronRight,
  SprayCan,
  Calculator,
  Mic,
  Radar
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { showToast } from './Toast';

const NAV_ITEMS = [
  { path: '/dashboard', label: 'Bảng Điều Khiển', icon: LayoutDashboard, badge: null },
  { path: '/diagnose', label: 'Chẩn Đoán AI', icon: ScanEye, badge: 'YOLO' },
  { path: '/diseases', label: 'Thư Viện Bệnh', icon: BookOpen, badge: null },
  { path: '/history', label: 'Lịch Sử Quét', icon: History, badge: null },
  { path: '/radar', label: 'Radar Dịch Bệnh', icon: Radar, badge: 'MỚI' },
  { path: '/treatments', label: 'Nhật Ký Điều Trị', icon: SprayCan, badge: null },
  { path: '/tools', label: 'Tính Liều & Cách Ly', icon: Calculator, badge: null },
  { path: '/assistant', label: 'Hỏi Đáp Giọng Nói', icon: Mic, badge: null },
];

interface SidebarProps {
  onItemClick?: () => void;
}

export function Sidebar({ onItemClick }: SidebarProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    showToast('info', 'Đã đăng xuất thành công.');
    navigate('/login');
  };

  return (
    <aside className="w-64 h-full bg-white/85 backdrop-blur-md border-r border-[#E2EFE7]/80 flex flex-col justify-between shrink-0 select-none">
      {/* Top Section */}
      <div className="flex flex-col">
        {/* Brand Logo Header */}
        <div
          onClick={() => {
            navigate('/dashboard');
            onItemClick?.();
          }}
          className="p-6 flex items-center gap-3.5 cursor-pointer group border-b border-[#E2EFE7]/60"
        >
          <div className="w-11 h-11 rounded-xl bg-[#15803D] flex items-center justify-center text-white shadow-sm shadow-emerald-900/10 group-hover:scale-105 transition-transform">
            <Leaf className="w-6 h-6 text-white" />
          </div>
          <div className="min-w-0">
            <div className="font-extrabold text-lg tracking-tight text-[#0F172A] flex items-center gap-1.5 font-['Space_Grotesk']">
              LEAF_AI
            </div>
            <p className="text-[11px] font-semibold tracking-wider uppercase text-emerald-800 -mt-0.5 truncate">
              Bệnh Học Cây Trồng AI
            </p>
          </div>
        </div>

        {/* Navigation Items */}
        <div className="p-4 space-y-1.5">
          <div className="px-3 py-2 text-[11px] font-bold uppercase tracking-wider text-slate-400">
            Danh Mục Hệ Thống
          </div>
          {NAV_ITEMS.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onItemClick}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-all duration-150 ${
                  isActive
                    ? 'bg-[#F0FDF4] text-[#15803D] font-bold shadow-xs border border-emerald-200/70'
                    : 'text-slate-600 hover:text-[#0F172A] hover:bg-slate-50'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    size={18}
                    className={isActive ? 'text-[#15803D]' : 'text-slate-400'}
                  />
                  <span>{item.label}</span>
                </div>
                {item.badge ? (
                  <span className="text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-emerald-100 text-[#15803D] font-mono">
                    {item.badge}
                  </span>
                ) : isActive ? (
                  <ChevronRight size={14} className="text-[#15803D]" />
                ) : null}
              </NavLink>
            );
          })}
        </div>
      </div>

      {/* Bottom Section: AI Engine Status & Profile */}
      <div className="p-4 space-y-3 border-t border-[#E2EFE7]/60">
        {/* Model Status Card */}
        <div className="p-3.5 rounded-xl bg-[#F0FDF4] border border-emerald-200/70 text-xs">
          <div className="flex items-center justify-between">
            <span className="font-bold text-[#15803D] flex items-center gap-1.5">
              <Sparkles size={14} className="text-emerald-600" />
              Động Cơ Thị Giác YOLO
            </span>
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-800">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Hoạt Động
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1 leading-snug">
            Chẩn đoán bệnh lá chè · thư viện bệnh sầu riêng, măng cụt, chôm chôm
          </p>
        </div>

        {/* User Profile & Sign Out */}
        <div className="pt-1 flex items-center justify-between">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-9 h-9 rounded-full bg-[#15803D] text-white flex items-center justify-center font-bold text-xs shrink-0 shadow-xs">
              {user?.email?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-bold text-slate-900 truncate" title={user?.email}>
                {user?.email ? user.email.split('@')[0] : 'Kỹ Sư Nông Học'}
              </p>
              <p className="text-[10px] text-slate-400 truncate font-mono">
                {user?.email || 'Đã Đăng Nhập'}
              </p>
            </div>
          </div>

          <button
            onClick={handleLogout}
            title="Đăng xuất khỏi tài khoản"
            aria-label="Đăng xuất"
            className="w-8 h-8 rounded-lg text-slate-400 hover:text-red-600 hover:bg-red-50 flex items-center justify-center transition-colors cursor-pointer"
          >
            <LogOut size={16} />
          </button>
        </div>
      </div>
    </aside>
  );
}

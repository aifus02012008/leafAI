import { useNavigate, useLocation } from 'react-router-dom';
import {
  Menu,
  ScanEye,
  LogOut,
  ChevronRight
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { showToast } from './Toast';
import { NotificationBell } from './NotificationBell';

const ROUTE_TITLES: Record<string, { title: string; subtitle: string }> = {
  '/dashboard': { title: 'Bảng Điều Khiển Nông Học', subtitle: 'Tổng quan sức khỏe lá cây trồng & dữ liệu giám sát' },
  '/diagnose': { title: 'Chẩn Đoán Bệnh Bằng AI', subtitle: 'Phát hiện bệnh lá cây trồng bằng học sâu theo thời gian thực' },
  '/diseases': { title: 'Thư Viện Bệnh Học Cây Trồng', subtitle: 'Tra cứu bệnh hại chè, sầu riêng, măng cụt, chôm chôm' },
  '/history': { title: 'Lịch Sử Chẩn Đoán', subtitle: 'Hồ sơ quét, định vị tổn thương & báo cáo canh tác' },
  '/farms': { title: 'Vườn & Thông Báo', subtitle: 'Vườn theo dõi, cảnh báo dịch bệnh & quyền riêng tư' },
  '/radar': { title: 'Radar Dịch Bệnh', subtitle: 'Cảnh báo sớm từ ca bệnh quanh vườn & dự báo thời tiết' },
  '/treatments': { title: 'Nhật Ký Điều Trị', subtitle: 'Theo dõi hiệu quả thuốc & thời gian cách ly' },
  '/tools': { title: 'Công Cụ Phun Thuốc', subtitle: 'Tính liều pha, chi phí & ngày được thu hoạch' },
  '/assistant': { title: 'Hỏi Đáp Giọng Nói', subtitle: 'Hỏi về bệnh cây bằng tiếng Việt' },
};

interface HeaderProps {
  onToggleMobileSidebar?: () => void;
}

export function Header({ onToggleMobileSidebar }: HeaderProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const currentRoute = ROUTE_TITLES[location.pathname] || {
    title: 'Nền Tảng LEAF_AI',
    subtitle: 'Hệ thống nhận diện bệnh hại cây trồng',
  };

  const handleLogout = () => {
    logout();
    showToast('info', 'Đã đăng xuất thành công.');
    navigate('/login');
  };

  return (
    <header className="w-full h-18 px-4 sm:px-8 bg-white/85 backdrop-blur-md border-b border-[#E2EFE7]/80 flex items-center justify-between sticky top-0 z-30 shadow-xs">
      {/* Left: Mobile Toggle & Page Breadcrumbs */}
      <div className="flex items-center gap-3.5 min-w-0">
        {onToggleMobileSidebar && (
          <button
            onClick={onToggleMobileSidebar}
            aria-label="Mở thanh điều hướng"
            className="md:hidden p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <Menu size={20} />
          </button>
        )}

        <div className="hidden sm:flex items-center gap-2 text-xs text-slate-400 font-medium">
          <span className="text-slate-500 hover:text-emerald-700 cursor-pointer" onClick={() => navigate('/dashboard')}>
            LEAF_AI
          </span>
          <ChevronRight size={13} className="text-slate-300" />
          <span className="font-bold text-[#15803D]">
            {currentRoute.title}
          </span>
        </div>

        <div className="sm:hidden font-bold text-base text-slate-900 truncate font-['Space_Grotesk']">
          {currentRoute.title}
        </div>
      </div>

      {/* Right: Actions, Model Status Pill, User Info */}
      <div className="flex items-center gap-3">
        {/* Model status indicator (desktop) */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F0FDF4] border border-emerald-200/80 text-xs font-semibold text-[#15803D]">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>YOLOv11 Sẵn Sàng</span>
        </div>

        {/* Quick action button */}
        {location.pathname !== '/diagnose' && (
          <button
            onClick={() => navigate('/diagnose')}
            className="btn-primary text-xs py-2 px-3.5 hidden sm:inline-flex"
          >
            <ScanEye size={15} />
            <span>Quét Lá Cây</span>
          </button>
        )}

        <NotificationBell />

        {/* User avatar circle */}
        <div
          title={user?.email || 'Hồ sơ người dùng'}
          className="w-9 h-9 rounded-full bg-emerald-50 border border-emerald-200 text-[#15803D] font-bold text-xs flex items-center justify-center cursor-default shadow-xs"
        >
          {user?.email?.charAt(0).toUpperCase() || 'U'}
        </div>

        {/* Quick logout */}
        <button
          onClick={handleLogout}
          title="Đăng xuất"
          aria-label="Đăng xuất"
          className="w-9 h-9 rounded-xl border border-[#E2EFE7] hover:border-red-200 hover:bg-red-50 text-slate-500 hover:text-red-600 flex items-center justify-center transition-colors cursor-pointer"
        >
          <LogOut size={16} />
        </button>
      </div>
    </header>
  );
}

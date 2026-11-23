import { useState } from 'react';
import { Outlet, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Header } from '../components/Header';
import { Sidebar } from '../components/Sidebar';
import { LoadingState } from '../components/LoadingState';
import { ChatBubble } from '../components/assistant/ChatBubble';
import { X } from 'lucide-react';

export function AppLayout() {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  if (loading) {
    return (
      <div className="min-h-screen w-full bg-transparent flex items-center justify-center p-8">
        <LoadingState message="Đang xác thực phiên làm việc..." size={40} />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-transparent text-[#10201A] flex overflow-x-hidden font-sans">
      {/* Desktop Persistent Sidebar */}
      <div className="hidden md:flex h-screen sticky top-0 shrink-0 z-40">
        <Sidebar />
      </div>

      {/* Mobile Drawer Backdrop & Drawer */}
      {mobileSidebarOpen && (
        <div className="fixed inset-0 z-50 md:hidden flex">
          {/* Backdrop */}
          <div
            onClick={() => setMobileSidebarOpen(false)}
            className="fixed inset-0 bg-forest/60 transition-opacity duration-200"
            aria-hidden="true"
          />

          {/* Drawer Panel */}
          <div className="relative w-64 max-w-[85vw] h-full bg-forest shadow-2xl z-10 flex flex-col animate-in slide-in-from-left duration-200">
            <button
              onClick={() => setMobileSidebarOpen(false)}
              aria-label="Đóng menu"
              className="absolute top-4 right-4 p-2 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors z-20 cursor-pointer"
            >
              <X size={18} />
            </button>
            <Sidebar onItemClick={() => setMobileSidebarOpen(false)} />
          </div>
        </div>
      )}

      {/* Main Content Workspace */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        {/* Top Header Navigation */}
        <Header onToggleMobileSidebar={() => setMobileSidebarOpen(true)} />

        {/* Dynamic Page Container */}
        <main className="flex-1 px-4 sm:px-8 lg:px-10 py-6 sm:py-8 overflow-y-auto">
          <div className="max-w-7xl mx-auto w-full">
            <div key={location.pathname} className="page-slide-in">
              <Outlet />
            </div>
          </div>
        </main>
      </div>

      <ChatBubble />
    </div>
  );
}

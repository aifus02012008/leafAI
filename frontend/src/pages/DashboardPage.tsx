import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Camera, Radar, SprayCan, Mic, ArrowRight, type LucideIcon } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { apiGetDashboardStats } from '../api/dashboard';
import { resolveMediaUrl } from '../api/client';
import { LoadingState } from '../components/LoadingState';
import { EmptyState } from '../components/EmptyState';
import type { DashboardStats } from '../types';

const CHART_PALETTE = ['#1F7A4D', '#2E9A63', '#5EE6A0', '#17603C', '#F2C94C', '#C99A16'];

const SHORTCUTS: readonly { to: string; label: string; icon: LucideIcon }[] = [
  { to: '/radar', label: 'Radar', icon: Radar },
  { to: '/treatments', label: 'Điều trị', icon: SprayCan },
  { to: '/assistant', label: 'Hỏi đáp', icon: Mic },
];

function cleanName(raw: string): string {
  return raw.replace('Tomato___', '').replace(/_/g, ' ');
}

function Metric({ label, value, tone }: { label: string; value: number; tone: 'ink' | 'sun' | 'leaf' }) {
  const color = tone === 'sun' ? 'text-[#B8860B]' : tone === 'leaf' ? 'text-leaf' : 'text-ink';
  return (
    <div className="clean-card px-5 py-4">
      <p className={`font-display text-3xl font-extrabold ${color}`}>{value}</p>
      <p className="text-xs font-medium text-ink/55 mt-0.5">{label}</p>
    </div>
  );
}

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    apiGetDashboardStats()
      .then(setStats)
      .catch(() => setStats(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState message="Đang tải…" />;
  if (!stats) return <EmptyState title="Không tải được dữ liệu" description="Kiểm tra kết nối rồi tải lại trang." />;

  const chartData = Object.entries(stats.disease_distribution).map(([name, count]) => ({ name: cleanName(name), count }));

  return (
    <div className="space-y-6">
      {/* Primary action + shortcuts */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
        <button
          type="button"
          onClick={() => navigate('/diagnose')}
          className="col-span-3 sm:col-span-3 rounded-[18px] bg-forest text-white p-6 flex items-center gap-4 text-left hover:bg-forest-2 transition-colors cursor-pointer"
        >
          <span className="w-14 h-14 rounded-2xl bg-mint text-forest flex items-center justify-center shrink-0">
            <Camera size={26} />
          </span>
          <span className="font-display text-2xl font-extrabold">Chụp lá</span>
          <ArrowRight size={22} className="ml-auto text-mint" />
        </button>
        {SHORTCUTS.map(({ to, label, icon: Icon }) => (
          <Link
            key={to}
            to={to}
            className="clean-card clean-card-hover p-4 flex flex-col items-center justify-center gap-2 text-sm font-semibold text-ink"
          >
            <Icon size={22} className="text-leaf" />
            {label}
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-3">
        <Metric label="Lượt quét" value={stats.total_diagnoses} tone="ink" />
        <Metric label="Có bệnh" value={stats.detected_count} tone="sun" />
        <Metric label="Khoẻ" value={stats.no_detection_count} tone="leaf" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <section className="lg:col-span-7 clean-card p-6" aria-labelledby="chart-title">
          <h2 id="chart-title" className="font-display text-base font-bold text-ink">Bệnh hay gặp</h2>
          {chartData.length > 0 ? (
            <div className="h-72 w-full pt-4">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 30 }}>
                  <XAxis dataKey="name" tick={{ fill: '#5B6B62', fontSize: 11 }} interval={0} angle={-20} textAnchor="end" />
                  <YAxis tick={{ fill: '#5B6B62', fontSize: 11 }} allowDecimals={false} />
                  <Tooltip
                    contentStyle={{ borderColor: '#DCE5DC', borderRadius: 12, color: '#10201A', fontSize: 12, fontWeight: 600 }}
                  />
                  <Bar dataKey="count" name="Số lá" radius={[6, 6, 0, 0]}>
                    {chartData.map((_, i) => (
                      <Cell key={i} fill={CHART_PALETTE[i % CHART_PALETTE.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="py-16 text-center text-sm text-ink/40">Chưa có dữ liệu</p>
          )}
        </section>

        <section className="lg:col-span-5 clean-card p-6" aria-labelledby="recent-title">
          <div className="flex items-center justify-between">
            <h2 id="recent-title" className="font-display text-base font-bold text-ink">Gần đây</h2>
            <Link to="/history" className="text-xs font-bold text-leaf hover:text-leaf-dark flex items-center gap-1">
              Tất cả <ArrowRight size={13} />
            </Link>
          </div>
          <div className="space-y-2 pt-4">
            {stats.recent_diagnoses.length > 0 ? (
              stats.recent_diagnoses.map((item) => {
                const sick = item.status === 'detected';
                return (
                  <Link
                    key={item.id}
                    to="/history"
                    className="p-2.5 rounded-2xl hover:bg-leaf-wash flex items-center gap-3 transition-colors"
                  >
                    <img
                      src={resolveMediaUrl(item.original_image_url)}
                      alt=""
                      className="w-12 h-12 rounded-xl object-cover bg-paper shrink-0"
                    />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-semibold text-ink truncate">
                        {item.primary_disease ? cleanName(item.primary_disease) : sick ? 'Có bệnh' : 'Lá khoẻ'}
                      </p>
                      <p className="text-[11px] text-ink/50 font-mono">
                        {item.created_at ? new Date(item.created_at).toLocaleDateString('vi-VN') : ''}
                      </p>
                    </div>
                    <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${sick ? 'bg-sun' : 'bg-mint'}`} aria-label={sick ? 'Có bệnh' : 'Khoẻ'} />
                  </Link>
                );
              })
            ) : (
              <p className="py-16 text-center text-sm text-ink/40">Chưa có lượt quét</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}

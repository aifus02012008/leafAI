import { CloudRain, Droplets, SprayCan, Thermometer, Wind } from 'lucide-react';
import { formatDate } from '../../utils/format';
import type { DayWeather, SprayWindow } from '../../types';

const WEEKDAY = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7'];
const WET_HUMID_HOURS = 6;
const WET_RAIN_MM = 5;

interface WeatherForecastProps {
  days: readonly DayWeather[] | null | undefined;
  recentRainMm?: number | null;
  sprayWindows?: readonly SprayWindow[];
}

function dayLabel(iso: string): string {
  return `${WEEKDAY[new Date(`${iso}T00:00:00`).getDay()]} ${formatDate(iso).slice(0, 5)}`;
}

function windowLabel(w: SprayWindow): string {
  const start = new Date(w.start);
  const end = new Date(w.end);
  const hh = (d: Date) => String(d.getHours()).padStart(2, '0');
  return `${WEEKDAY[start.getDay()]} ${hh(start)}–${hh(end)}h`;
}

/** 7-day outlook, rain already fallen, and the best spraying times in the next 48 h. */
export function WeatherForecast({ days, recentRainMm, sprayWindows = [] }: WeatherForecastProps) {
  if (!days || days.length === 0) {
    return <p className="text-xs text-slate-500">Chưa có dự báo</p>;
  }
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2 text-xs">
        <span
          className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-semibold ${
            sprayWindows.length ? 'bg-leaf-wash text-leaf' : 'bg-paper text-slate-500'
          }`}
          title="Không mưa ít nhất 3 giờ sau khi phun, gió nhẹ, sáng sớm hoặc chiều mát"
        >
          <SprayCan size={13} />
          {sprayWindows.length ? `Giờ phun tốt: ${sprayWindows.map(windowLabel).join(' · ')}` : 'Chưa có giờ phun tốt trong 48h'}
        </span>
        {recentRainMm != null && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-paper px-2.5 py-1 font-semibold text-slate-600" title="Tổng lượng mưa 3 ngày vừa qua">
            <CloudRain size={13} /> 3 ngày qua: {Math.round(recentRainMm)} mm
          </span>
        )}
      </div>

      <ul className="space-y-1 text-xs" aria-label="Dự báo 7 ngày">
        {days.map((d, i) => {
          const wet = d.humid_hours >= WET_HUMID_HOURS || d.precip_mm >= WET_RAIN_MM;
          return (
            <li
              key={d.day}
              className={`grid grid-cols-[3.3rem_2.3rem_3.7rem_1fr_2.4rem] items-center gap-1 px-2 sm:px-2.5 whitespace-nowrap py-1.5 rounded-lg border ${
                wet ? 'bg-sky-50 border-sky-200' : 'bg-white border-[#DCE5DC]'
              } ${i >= 3 ? 'opacity-75' : ''}`}
            >
              <span className="font-bold text-slate-800">{dayLabel(d.day)}</span>
              <span className="flex items-center gap-0.5 text-sky-700" title="Số giờ độ ẩm ≥ 90%">
                <Droplets size={11} />
                {d.humid_hours}h
              </span>
              <span className="flex items-center gap-0.5 text-slate-600">
                <Thermometer size={11} />
                {Math.round(d.t_min)}–{Math.round(d.t_max)}°
              </span>
              <span className="flex items-center gap-0.5 text-slate-600" title="Lượng mưa (xác suất cao nhất trong ngày)">
                <CloudRain size={11} />
                {d.precip_mm} mm{d.rain_prob_max != null ? ` · ${d.rain_prob_max}%` : ''}
              </span>
              <span className="flex items-center gap-0.5 text-slate-500" title="Gió mạnh nhất (km/h)">
                <Wind size={11} />
                {d.wind_max != null ? Math.round(d.wind_max) : '–'}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

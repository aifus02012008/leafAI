"""Find good spraying windows in an hourly forecast (pure, no I/O).

A good hour for spraying: early morning or late afternoon, no rain now and for the next few hours
(so the product dries on the leaf), light wind (little drift) and moderate temperature.
⚠️ Thresholds follow common label guidance; check the product label for its own limits.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

SPRAY_HOURS = (5, 6, 7, 8, 9, 15, 16, 17)   # local hour at which spraying may START
RAIN_FREE_AFTER_H = 3                        # dry hours needed after spraying
MAX_RAIN_PROB = 30                           # %
MAX_WIND_KMH = 12.0
TEMP_RANGE = (15.0, 33.0)
MIN_WINDOW_H = 2
MAX_WINDOWS = 3
HORIZON_H = 48


@dataclass(frozen=True)
class HourWeather:
    time: datetime
    temp: float
    rain_mm: float
    rain_prob: int | None
    wind_kmh: float | None


@dataclass(frozen=True)
class SprayWindow:
    start: datetime
    end: datetime          # exclusive


def _dry(h: HourWeather) -> bool:
    return h.rain_mm < 0.1 and (h.rain_prob is None or h.rain_prob <= MAX_RAIN_PROB)


def _good_start(hours: list[HourWeather], i: int) -> bool:
    h = hours[i]
    if h.time.hour not in SPRAY_HOURS:
        return False
    if not (TEMP_RANGE[0] <= h.temp <= TEMP_RANGE[1]):
        return False
    if h.wind_kmh is not None and h.wind_kmh > MAX_WIND_KMH:
        return False
    following = hours[i:i + 1 + RAIN_FREE_AFTER_H]
    return len(following) == 1 + RAIN_FREE_AFTER_H and all(_dry(x) for x in following)


def find_windows(hours: list[HourWeather], now: datetime) -> list[SprayWindow]:
    """Up to MAX_WINDOWS windows (>= MIN_WINDOW_H long) in the next HORIZON_H hours, earliest first."""
    ordered = sorted(hours, key=lambda h: h.time)
    horizon = now + timedelta(hours=HORIZON_H)
    windows: list[SprayWindow] = []
    run_start: datetime | None = None
    run_end: datetime | None = None
    for i, h in enumerate(ordered):
        if h.time < now or h.time >= horizon:
            continue
        if _good_start(ordered, i):
            if run_start is not None and run_end == h.time:
                run_end = h.time + timedelta(hours=1)
            else:
                if run_start is not None and run_end is not None:
                    windows.append(SprayWindow(run_start, run_end))
                run_start, run_end = h.time, h.time + timedelta(hours=1)
    if run_start is not None and run_end is not None:
        windows.append(SprayWindow(run_start, run_end))
    long_enough = [w for w in windows if (w.end - w.start) >= timedelta(hours=MIN_WINDOW_H)]
    return long_enough[:MAX_WINDOWS]

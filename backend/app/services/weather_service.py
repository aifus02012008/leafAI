"""Weather forecast from Open-Meteo (free, no API key) for the disease radar.

One request returns hourly humidity, temperature, rain, rain probability and wind for the past 3 days
and the next 7. From it we build:
- a per-day outlook (7 days shown to the farmer; the first 3 drive the risk score),
- the rain that already fell in the last 3 days (saturated soil favours Phytophthora),
- good spraying windows in the next 48 h (see spray_window).

Coordinates are rounded to 0.1° (~11 km) before the request: enough for weather,
avoids sending precise farm locations to a third party, and makes caching effective.
⚠️ Open-Meteo's free tier is for non-commercial use; a commercial plan is needed
before selling radar data.
"""
from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime

import httpx

from app.services.radar_rules import DayWeather
from app.services.spray_window import HourWeather, SprayWindow, find_windows

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_DAYS = 7
RISK_DAYS = 3            # risk score uses the near term only; further days are informational
PAST_DAYS = 3
CACHE_TTL_S = 3 * 3600
HUMID_RH = 90
HOURLY_VARS = "relative_humidity_2m,temperature_2m,precipitation,precipitation_probability,wind_speed_10m"


@dataclass(frozen=True)
class Forecast:
    days: list[DayWeather]                    # today onwards, up to FORECAST_DAYS
    recent_rain_mm: float | None = None       # total rain over the PAST_DAYS before today
    spray_windows: list[SprayWindow] = field(default_factory=list)

    @property
    def risk_days(self) -> list[DayWeather]:
        return self.days[:RISK_DAYS]


_cache: dict[tuple[float, float], tuple[float, Forecast]] = {}
_lock = threading.Lock()


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def _num(values: list, i: int) -> float | None:
    if i < len(values) and values[i] is not None:
        return float(values[i])
    return None


def _hours(payload: dict) -> list[HourWeather]:
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    rh = hourly.get("relative_humidity_2m") or []
    temp = hourly.get("temperature_2m") or []
    rain = hourly.get("precipitation") or []
    prob = hourly.get("precipitation_probability") or []
    wind = hourly.get("wind_speed_10m") or []
    rows = []
    for i, t in enumerate(times):
        humidity, temperature = _num(rh, i), _num(temp, i)
        if humidity is None or temperature is None:
            continue
        p = _num(prob, i)
        rows.append((t, humidity, HourWeather(
            time=datetime.fromisoformat(t),
            temp=temperature,
            rain_mm=_num(rain, i) or 0.0,
            rain_prob=int(p) if p is not None else None,
            wind_kmh=_num(wind, i),
        )))
    return rows  # type: ignore[return-value]


def _daily(rows: list) -> list[DayWeather]:
    buckets: dict[str, list] = defaultdict(list)
    for t, humidity, hour in rows:
        buckets[t[:10]].append((humidity, hour))
    days = []
    for day_str in sorted(buckets):
        items = buckets[day_str]
        probs = [h.rain_prob for _, h in items if h.rain_prob is not None]
        winds = [h.wind_kmh for _, h in items if h.wind_kmh is not None]
        days.append(DayWeather(
            day=date.fromisoformat(day_str),
            humid_hours=sum(1 for r, _ in items if r >= HUMID_RH),
            rh_max=max(r for r, _ in items),
            t_min=min(h.temp for _, h in items),
            t_max=max(h.temp for _, h in items),
            precip_mm=round(sum(h.rain_mm for _, h in items), 1),
            rain_prob_max=max(probs) if probs else None,
            wind_max=round(max(winds), 1) if winds else None,
        ))
    return days


def parse_forecast(payload: dict, today: date, now: datetime | None = None) -> Forecast:
    rows = _hours(payload)
    days = _daily(rows)
    past = [d for d in days if d.day < today]
    upcoming = [d for d in days if d.day >= today][:FORECAST_DAYS]
    recent = round(sum(d.precip_mm for d in past), 1) if past else None
    hours = [h for _, _, h in rows]
    windows = find_windows(hours, now or datetime.combine(today, datetime.min.time()))
    return Forecast(days=upcoming, recent_rain_mm=recent, spray_windows=windows)


def parse_hourly(payload: dict) -> list[DayWeather]:
    """Backward-compatible helper: daily outlook for every day in the payload (first RISK_DAYS)."""
    return _daily(_hours(payload))[:RISK_DAYS]


def get_forecast(lat: float, lng: float) -> Forecast | None:
    """7-day forecast + recent rain + spray windows, or None when Open-Meteo is unreachable."""
    key = (round(lat, 1), round(lng, 1))
    now = time.monotonic()
    with _lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_TTL_S:
            return hit[1]
    try:
        res = httpx.get(
            OPEN_METEO_URL,
            params={
                "latitude": key[0],
                "longitude": key[1],
                "hourly": HOURLY_VARS,
                "past_days": PAST_DAYS,
                "forecast_days": FORECAST_DAYS,
                "timezone": "Asia/Bangkok",
            },
            timeout=10.0,
        )
        res.raise_for_status()
        payload = res.json()
        local_now = datetime.now().replace(minute=0, second=0, microsecond=0)
        forecast = parse_forecast(payload if isinstance(payload, dict) else {}, local_now.date(), local_now)
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Weather forecast unavailable: %s", type(exc).__name__)
        return None
    if not forecast.days:
        return None
    with _lock:
        _cache[key] = (now, forecast)
    return forecast


def get_outlook(lat: float, lng: float) -> list[DayWeather] | None:
    """Near-term daily outlook used for risk scoring (alert job, radar)."""
    forecast = get_forecast(lat, lng)
    return forecast.risk_days if forecast else None

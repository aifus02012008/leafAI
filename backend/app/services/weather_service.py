"""3-day weather outlook from Open-Meteo (free, no API key), aggregated per day.

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
from datetime import date

import httpx

from app.services.radar_rules import DayWeather

logger = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_DAYS = 3
CACHE_TTL_S = 3 * 3600
HUMID_RH = 90

_cache: dict[tuple[float, float], tuple[float, list[DayWeather]]] = {}
_lock = threading.Lock()


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def parse_hourly(payload: dict) -> list[DayWeather]:
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    rh = hourly.get("relative_humidity_2m") or []
    temp = hourly.get("temperature_2m") or []
    rain = hourly.get("precipitation") or []
    buckets: dict[str, list[tuple[float, float, float]]] = defaultdict(list)
    for i, t in enumerate(times):
        if i < len(rh) and i < len(temp) and rh[i] is not None and temp[i] is not None:
            buckets[t[:10]].append((float(rh[i]), float(temp[i]), float(rain[i] or 0) if i < len(rain) else 0.0))
    days = []
    for day_str in sorted(buckets):
        rows = buckets[day_str]
        days.append(DayWeather(
            day=date.fromisoformat(day_str),
            humid_hours=sum(1 for r, _, _ in rows if r >= HUMID_RH),
            rh_max=max(r for r, _, _ in rows),
            t_min=min(t for _, t, _ in rows),
            t_max=max(t for _, t, _ in rows),
            precip_mm=round(sum(p for _, _, p in rows), 1),
        ))
    return days[:FORECAST_DAYS]


def get_outlook(lat: float, lng: float) -> list[DayWeather] | None:
    """Daily outlook for the next 3 days, or None when the weather service is unreachable."""
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
                "hourly": "relative_humidity_2m,temperature_2m,precipitation",
                "forecast_days": FORECAST_DAYS,
                "timezone": "Asia/Bangkok",
            },
            timeout=10.0,
        )
        res.raise_for_status()
        payload = res.json()
        days = parse_hourly(payload if isinstance(payload, dict) else {})
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Weather outlook unavailable: %s", exc)
        return None
    if not days:
        return None
    with _lock:
        _cache[key] = (now, days)
    return days

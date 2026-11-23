"""Disease radar: combine nearby confirmed cases with the weather outlook into a risk alert.

Pure functions only. Thresholds are initial assumptions pending agronomist validation:
fungal/oomycete/algal diseases spread with long leaf-wetness (RH >= 90%) and rain;
sap-sucking pests and mites build up in warm, dry spells.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

from app.services.disease_weather_rules import DRY_HOT, PHYTOPHTHORA, WeatherProfile, favourable_share, profile_for

Level = Literal["low", "medium", "high"]
Category = Literal["humid", "pest"]

PEST_KEYWORDS = ("rầy", "nhện", "bọ xít", "bọ trĩ", "psyllid", "leafhopper", "mite", "bug", "thrips")
WEEKDAYS_VI = ("Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật")

HUMID_DAY_HOURS = 6        # a day with >= 6 h at RH >= 90% counts as a wet (infection-favourable) day
CASES_HIGH = 8             # nearby cases in the window considered an active outbreak
CASES_MEDIUM = 3
LEVEL_LABEL = {"low": "thấp", "medium": "trung bình", "high": "cao"}


@dataclass(frozen=True)
class DayWeather:
    day: date
    humid_hours: int        # hours with RH >= 90%
    rh_max: float
    t_min: float
    t_max: float
    precip_mm: float
    rain_prob_max: int | None = None   # % (max hourly probability that day)
    wind_max: float | None = None      # km/h


@dataclass(frozen=True)
class NearbyCases:
    crop_code: str
    disease: str
    cases: int
    distinct_users: int
    weighted: float         # recency/confidence-weighted case count


@dataclass(frozen=True)
class RiskAlert:
    crop_code: str
    disease: str
    level: Level
    score: float
    cases: int
    message: str
    spray_before: date | None


def disease_category(disease: str) -> Category:
    name = disease.lower()
    return "pest" if any(k in name for k in PEST_KEYWORDS) else "humid"


def _case_score(cases: NearbyCases) -> float:
    if cases.weighted >= CASES_HIGH:
        return 1.0
    return min(cases.weighted / CASES_HIGH, 1.0)


def _weather_score(days: list[DayWeather], profile: WeatherProfile) -> float:
    """Share of forecast days favourable to this disease (per-disease profile, see disease_weather_rules)."""
    return favourable_share(days, profile)


def _first_favourable_day(days: list[DayWeather], after: date, profile: WeatherProfile) -> date | None:
    """First infection-favourable day strictly after `after` (preventive spraying must precede it)."""
    for d in days:
        if d.day > after and profile.favourable(d):
            return d.day
    return None


def _level(score: float) -> Level:
    if score >= 0.65:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def _weather_sentence(days: list[DayWeather] | None, profile: WeatherProfile) -> str:
    if days is None:
        return "Chưa lấy được dự báo thời tiết, mức nguy cơ chỉ dựa trên số ca bệnh."
    peak = max((d.humid_hours for d in days), default=0)
    rain = sum(d.precip_mm for d in days)
    favourable = sum(1 for d in days if profile.favourable(d))
    weather = f"{len(days)} ngày tới: ẩm ≥ 90% tối đa {peak} giờ/ngày, tổng mưa {rain:.0f} mm"
    if favourable:
        return f"{weather}; {favourable} ngày {profile.note}."
    return f"{weather}; thời tiết chưa thuận lợi cho bệnh này."


SOAKED_SOIL_MM = 30.0   # rain over the last 3 days that saturates soil (Phytophthora, root/collar rots)


def _recent_rain_bonus(profile: WeatherProfile, recent_rain_mm: float | None) -> float:
    if recent_rain_mm is None or recent_rain_mm < SOAKED_SOIL_MM or profile.kind != "wet":
        return 0.0
    return 0.2 if profile is PHYTOPHTHORA else 0.1


def assess_risk(
    cases: NearbyCases,
    days: list[DayWeather] | None,
    radius_km: float,
    today: date,
    recent_rain_mm: float | None = None,
) -> RiskAlert:
    profile = profile_for(cases.disease)
    sprayable = profile is not DRY_HOT  # preventive fungicide timing; pests are scouted, not pre-sprayed
    case_score = _case_score(cases)
    if days is None:
        score = case_score * 0.8
    else:
        weather = min(1.0, _weather_score(days, profile) + _recent_rain_bonus(profile, recent_rain_mm))
        score = 0.55 * case_score + 0.45 * weather
    level = _level(score)
    spray_before = _first_favourable_day(days, today, profile) if days and sprayable else None
    wet_today = bool(days) and sprayable and any(d.day == today and profile.favourable(d) for d in days)

    parts = [
        f"Trong bán kính {radius_km:g} km có {cases.cases} ca {cases.disease} trong 7 ngày qua."
        if cases.cases else f"Chưa ghi nhận ca {cases.disease} nào trong bán kính {radius_km:g} km.",
        _weather_sentence(days, profile),
        *([f"3 ngày qua đã mưa {recent_rain_mm:.0f} mm, đất còn ẩm."] if _recent_rain_bonus(profile, recent_rain_mm) else []),
        f"Nguy cơ lây lan {LEVEL_LABEL[level]}.",
    ]
    if level != "low" and spray_before:
        when = "ngay khi lá ráo và " if wet_today else ""
        parts.append(f"Nên phun phòng {when}trước {WEEKDAYS_VI[spray_before.weekday()]} ({spray_before:%d/%m}).")
    elif level != "low" and wet_today:
        parts.append("Nên phun phòng ngay khi lá ráo.")
    elif level != "low":
        parts.append("Nên kiểm tra vườn và chuẩn bị phương án phòng trừ.")
    return RiskAlert(
        crop_code=cases.crop_code,
        disease=cases.disease,
        level=level,
        score=round(score, 3),
        cases=cases.cases,
        message=" ".join(parts),
        spray_before=spray_before,
    )

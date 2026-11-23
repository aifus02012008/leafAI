"""Disease radar: combine nearby confirmed cases with the weather outlook into a risk alert.

Pure functions only. Thresholds are initial assumptions pending agronomist validation:
fungal/oomycete/algal diseases spread with long leaf-wetness (RH >= 90%) and rain;
sap-sucking pests and mites build up in warm, dry spells.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

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


def _weather_score(days: list[DayWeather], category: Category) -> float:
    if not days:
        return 0.0
    wet_days = sum(1 for d in days if d.humid_hours >= HUMID_DAY_HOURS or d.precip_mm >= 5)
    wet_share = wet_days / len(days)
    return (1.0 - wet_share) * 0.8 if category == "pest" else wet_share


def _is_wet(d: DayWeather) -> bool:
    return d.humid_hours >= HUMID_DAY_HOURS or d.precip_mm >= 5


def _first_wet_day(days: list[DayWeather], after: date) -> date | None:
    """First infection-favourable day strictly after `after` (spraying must precede it)."""
    for d in days:
        if d.day > after and _is_wet(d):
            return d.day
    return None


def _level(score: float) -> Level:
    if score >= 0.65:
        return "high"
    if score >= 0.35:
        return "medium"
    return "low"


def _weather_sentence(days: list[DayWeather] | None, category: Category) -> str:
    if days is None:
        return "Chưa lấy được dự báo thời tiết, mức nguy cơ chỉ dựa trên số ca bệnh."
    peak = max((d.humid_hours for d in days), default=0)
    rain = sum(d.precip_mm for d in days)
    if category == "pest":
        return f"{len(days)} ngày tới tổng lượng mưa {rain:.0f} mm; thời tiết khô nóng thuận lợi cho sâu hại."
    return f"{len(days)} ngày tới có ngày độ ẩm ≥ 90% kéo dài {peak} giờ, tổng mưa {rain:.0f} mm."


def assess_risk(
    cases: NearbyCases,
    days: list[DayWeather] | None,
    radius_km: float,
    today: date,
) -> RiskAlert:
    category = disease_category(cases.disease)
    case_score = _case_score(cases)
    if days is None:
        score = case_score * 0.8
    else:
        score = 0.55 * case_score + 0.45 * _weather_score(days, category)
    level = _level(score)
    spray_before = _first_wet_day(days, today) if days and category == "humid" else None
    wet_today = bool(days) and category == "humid" and any(d.day == today and _is_wet(d) for d in days)

    parts = [
        f"Trong bán kính {radius_km:g} km có {cases.cases} ca {cases.disease} trong 7 ngày qua."
        if cases.cases else f"Chưa ghi nhận ca {cases.disease} nào trong bán kính {radius_km:g} km.",
        _weather_sentence(days, category),
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

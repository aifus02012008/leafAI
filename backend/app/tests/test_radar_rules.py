"""Unit tests for radar geo helpers and risk rules (pure functions)."""
from datetime import date

import pytest

from app.services.geo import bounding_box, haversine_km
from app.services.radar_rules import (
    DayWeather,
    NearbyCases,
    assess_risk,
    disease_category,
)


# ---------- geo ----------

def test_haversine_known_distance():
    # Hà Nội (Hoàn Kiếm) -> Bắc Giang city ≈ 47 km
    assert haversine_km(21.0285, 105.8542, 21.2731, 106.1946) == pytest.approx(43.8, abs=3)


def test_haversine_zero():
    assert haversine_km(10.0, 106.0, 10.0, 106.0) == 0


def test_bounding_box_contains_radius():
    lat_min, lat_max, lng_min, lng_max = bounding_box(21.0, 106.0, 5)
    assert lat_min < 21.0 < lat_max and lng_min < 106.0 < lng_max
    assert haversine_km(21.0, 106.0, lat_max, 106.0) == pytest.approx(5, rel=0.02)


# ---------- category ----------

@pytest.mark.parametrize("name,expected", [
    ("Rầy phấn trắng hại sầu riêng (Durian psyllid)", "pest"),
    ("Lá chè bị nhện đỏ gây hại (Red spider mite infested tea leaf)", "pest"),
    ("Cháy lá do Phytophthora trên sầu riêng (Durian Phytophthora leaf blight)", "humid"),
    ("Thán thư chôm chôm (Rambutan anthracnose)", "humid"),
])
def test_disease_category(name, expected):
    assert disease_category(name) == expected


# ---------- risk ----------

def _days(humid_hours: list[int], rain: list[float] | None = None) -> list[DayWeather]:
    rain = rain or [0.0] * len(humid_hours)
    start = date(2026, 11, 26)  # Thursday
    return [
        DayWeather(day=date.fromordinal(start.toordinal() + i), humid_hours=h, rh_max=95 if h else 70,
                   t_min=20, t_max=28, precip_mm=r)
        for i, (h, r) in enumerate(zip(humid_hours, rain))
    ]


def _cases(n: int, users: int) -> NearbyCases:
    return NearbyCases(crop_code="durian", disease="Cháy lá do Phytophthora trên sầu riêng (Durian Phytophthora leaf blight)",
                       cases=n, distinct_users=users, weighted=float(n))


def test_many_cases_and_humid_forecast_is_high_risk_with_message():
    alert = assess_risk(_cases(12, 6), _days([10, 14, 8]), radius_km=5, today=date(2026, 11, 25))
    assert alert.level == "high"
    assert "12 ca" in alert.message
    assert "5 km" in alert.message
    assert "Thứ Năm" in alert.message  # advise spraying before the first humid day


def test_few_cases_dry_weather_is_low_risk():
    alert = assess_risk(_cases(1, 1), _days([0, 0, 0]), radius_km=5, today=date(2026, 11, 25))
    assert alert.level == "low"


def test_weather_alone_can_raise_risk_without_cases():
    alert = assess_risk(_cases(0, 0), _days([16, 18, 12], rain=[12, 20, 5]), radius_km=5, today=date(2026, 11, 25))
    assert alert.level == "medium"


def test_pests_are_favoured_by_dry_weather():
    pest = NearbyCases(crop_code="durian", disease="Rầy phấn trắng hại sầu riêng (Durian psyllid)",
                       cases=8, distinct_users=4, weighted=8.0)
    dry = assess_risk(pest, _days([0, 0, 0]), radius_km=5, today=date(2026, 11, 25))
    wet = assess_risk(pest, _days([18, 18, 18], rain=[30, 30, 30]), radius_km=5, today=date(2026, 11, 25))
    assert ["low", "medium", "high"].index(dry.level) >= ["low", "medium", "high"].index(wet.level)


def test_no_weather_data_still_returns_case_based_alert():
    alert = assess_risk(_cases(12, 6), None, radius_km=5, today=date(2026, 11, 25))
    assert alert.level in ("medium", "high")
    assert "thời tiết" in alert.message.lower()


def test_wet_today_advises_spraying_before_next_wet_day():
    today = date(2026, 11, 23)  # Monday
    days = [DayWeather(date(2026, 11, 23 + i), 12, 96, 24, 31, 3.0) for i in range(3)]
    alert = assess_risk(_cases(12, 6), days, radius_km=5, today=today)
    assert alert.spray_before == date(2026, 11, 24)
    assert "ngay khi lá ráo" in alert.message and "Thứ Ba" in alert.message

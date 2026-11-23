"""Per-disease weather profiles used by the outbreak radar."""
from dataclasses import dataclass
from datetime import date

import pytest

from app.db.seed import durian, mangosteen, rambutan, tea
from app.services import disease_weather_rules as rules
from app.services.radar_rules import DayWeather, NearbyCases, assess_risk


@dataclass(frozen=True)
class Day:
    humid_hours: int
    t_min: float
    t_max: float
    precip_mm: float


RAINY = Day(humid_hours=12, t_min=24, t_max=29, precip_mm=25)
DRY_HOT = Day(humid_hours=0, t_min=26, t_max=35, precip_mm=0)
HUMID_NIGHTS = Day(humid_hours=6, t_min=21, t_max=29, precip_mm=0)


@pytest.mark.parametrize(
    "disease, profile",
    [
        (durian.PHYTOPHTHORA, rules.PHYTOPHTHORA),
        (durian.ANTHRACNOSE, rules.ANTHRACNOSE),
        (durian.ALGAL, rules.ALGAL),
        (durian.PSYLLID, rules.DRY_HOT),
        (durian.PHOMOPSIS, rules.LEAF_SPOT),
        (mangosteen.SOOTY_MOLD, rules.DRY_HOT),
        (mangosteen.PESTALOTIOPSIS, rules.LEAF_SPOT),
        (rambutan.POWDERY_MILDEW, rules.POWDERY),
        ("Gỉ sắt lá chè (Leaf rust of tea)", rules.RUST),
        ("Lá chè bị nhện đỏ gây hại (Red spider mite infested tea leaf)", rules.DRY_HOT),
        ("Một bệnh chưa biết", rules.DEFAULT),
    ],
)
def test_profile_matching(disease, profile):
    assert rules.profile_for(disease) is profile


def test_every_library_disease_has_a_specific_profile():
    for module, attr in ((durian, "DURIAN_DISEASES"), (mangosteen, "MANGOSTEEN_DISEASES"), (rambutan, "RAMBUTAN_DISEASES"), (tea, "TEA_DISEASES")):
        for entry in getattr(module, attr, []):
            assert rules.profile_for(entry["class_name"]) is not rules.DEFAULT, entry["class_name"]


def test_phytophthora_needs_heavy_rain_not_just_drizzle():
    assert rules.PHYTOPHTHORA.favourable(RAINY)
    assert not rules.PHYTOPHTHORA.favourable(Day(humid_hours=4, t_min=24, t_max=30, precip_mm=3))


def test_powdery_mildew_likes_dry_days_with_humid_nights_and_hates_downpours():
    assert rules.POWDERY.favourable(HUMID_NIGHTS)
    assert not rules.POWDERY.favourable(RAINY)


def test_pests_prefer_dry_heat():
    assert rules.DRY_HOT.favourable(DRY_HOT)
    assert not rules.DRY_HOT.favourable(RAINY)


def test_temperature_band_blocks_out_of_range_days():
    cold_wet = Day(humid_hours=12, t_min=12, t_max=18, precip_mm=20)
    assert not rules.ANTHRACNOSE.favourable(cold_wet)


def test_favourable_share():
    assert rules.favourable_share([RAINY, DRY_HOT], rules.ANTHRACNOSE) == 0.5
    assert rules.favourable_share([], rules.ANTHRACNOSE) == 0.0


def _days(*specs):
    return [DayWeather(day=date(2026, 11, 24 + i), humid_hours=s.humid_hours, rh_max=95, t_min=s.t_min, t_max=s.t_max, precip_mm=s.precip_mm) for i, s in enumerate(specs)]


def test_radar_uses_disease_profile_for_score_and_spray_date():
    cases = NearbyCases(crop_code="rambutan", disease=rambutan.POWDERY_MILDEW, cases=5, distinct_users=3, weighted=5)
    today = date(2026, 11, 24)
    humid_nights = assess_risk(cases, _days(HUMID_NIGHTS, HUMID_NIGHTS, HUMID_NIGHTS), 5, today)
    downpours = assess_risk(cases, _days(RAINY, RAINY, RAINY), 5, today)
    assert humid_nights.score > downpours.score
    assert humid_nights.spray_before == date(2026, 11, 25)
    assert "phấn trắng" in humid_nights.message


def test_radar_does_not_suggest_preventive_spray_for_pests():
    cases = NearbyCases(crop_code="durian", disease=durian.PSYLLID, cases=9, distinct_users=4, weighted=9)
    alert = assess_risk(cases, _days(DRY_HOT, DRY_HOT, DRY_HOT), 5, date(2026, 11, 24))
    assert alert.level == "high" and alert.spray_before is None

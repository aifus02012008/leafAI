"""7-day forecast parsing, recent rain, spray windows and their effect on radar risk."""
from datetime import date, datetime, timedelta

from app.db.seed import durian, rambutan
from app.services import weather_service
from app.services.radar_rules import DayWeather, NearbyCases, assess_risk
from app.services.spray_window import HourWeather, find_windows

TODAY = date(2026, 11, 24)


def _payload(hours: list[tuple[str, float, float, float, int, float]]) -> dict:
    """(time, rh, temp, rain, prob, wind) rows -> Open-Meteo hourly payload."""
    keys = ("time", "relative_humidity_2m", "temperature_2m", "precipitation", "precipitation_probability", "wind_speed_10m")
    return {"hourly": {k: [row[i] for row in hours] for i, k in enumerate(keys)}}


def _day_rows(day: date, rh: float, temp: float, rain: float, prob: int, wind: float):
    return [(f"{day.isoformat()}T{h:02d}:00", rh, temp, rain, prob, wind) for h in range(24)]


def test_parse_forecast_splits_past_and_future():
    rows = []
    for offset in (-3, -2, -1):
        rows += _day_rows(TODAY + timedelta(days=offset), 95, 26, 1.0, 80, 5)  # 24 mm/day
    for offset in range(7):
        rows += _day_rows(TODAY + timedelta(days=offset), 70, 28, 0.0, 10, 6)
    fc = weather_service.parse_forecast(_payload(rows), TODAY, datetime(2026, 11, 24, 4))
    assert [d.day for d in fc.days] == [TODAY + timedelta(days=i) for i in range(7)]
    assert fc.recent_rain_mm == 72.0
    assert len(fc.risk_days) == 3
    assert fc.days[0].rain_prob_max == 10 and fc.days[0].wind_max == 6
    assert fc.spray_windows, "dry calm mornings should give spray windows"


def _hours(start: datetime, n: int, **kw) -> list[HourWeather]:
    base = dict(temp=26.0, rain_mm=0.0, rain_prob=10, wind_kmh=5.0)
    base.update(kw)
    return [HourWeather(time=start + timedelta(hours=i), **base) for i in range(n)]


def test_spray_windows_are_morning_or_late_afternoon_and_dry():
    now = datetime(2026, 11, 24, 0)
    windows = find_windows(_hours(now, 48), now)
    assert windows[0].start == datetime(2026, 11, 24, 5)
    assert windows[0].end == datetime(2026, 11, 24, 10)
    assert all(w.start.hour in (5, 15) for w in windows)
    assert len(windows) <= 3


def test_no_window_when_rain_follows_or_wind_is_strong():
    now = datetime(2026, 11, 24, 0)
    rainy = _hours(now, 48, rain_mm=2.0, rain_prob=90)
    windy = _hours(now, 48, wind_kmh=25.0)
    assert find_windows(rainy, now) == []
    assert find_windows(windy, now) == []


def test_rain_just_after_spraying_cuts_the_window():
    now = datetime(2026, 11, 24, 0)
    hours = _hours(now, 48)
    hours[8] = HourWeather(datetime(2026, 11, 24, 8), 26.0, 3.0, 80, 5.0)  # shower at 08:00
    first = find_windows(hours, now)[0]
    # 05-07 starts would be rained on at 08:00 and a lone 09:00 slot is too short: first window is the afternoon.
    assert (first.start, first.end) == (datetime(2026, 11, 24, 15), datetime(2026, 11, 24, 18))


def _days(n: int, **kw) -> list[DayWeather]:
    base = dict(humid_hours=2, rh_max=85, t_min=24, t_max=30, precip_mm=0.0)
    base.update(kw)
    return [DayWeather(day=TODAY + timedelta(days=i + 1), **base) for i in range(n)]


def test_soaked_soil_raises_phytophthora_risk_and_is_mentioned():
    cases = NearbyCases("durian", durian.PHYTOPHTHORA, cases=4, distinct_users=3, weighted=4)
    dry = assess_risk(cases, _days(3), 5, TODAY, recent_rain_mm=0)
    soaked = assess_risk(cases, _days(3), 5, TODAY, recent_rain_mm=60)
    assert soaked.score > dry.score
    assert "3 ngày qua đã mưa 60 mm" in soaked.message


def test_recent_rain_does_not_affect_powdery_mildew():
    cases = NearbyCases("rambutan", rambutan.POWDERY_MILDEW, cases=4, distinct_users=3, weighted=4)
    a = assess_risk(cases, _days(3), 5, TODAY, recent_rain_mm=0)
    b = assess_risk(cases, _days(3), 5, TODAY, recent_rain_mm=60)
    assert a.score == b.score

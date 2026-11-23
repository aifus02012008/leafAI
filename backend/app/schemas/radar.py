from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel


class DayWeatherOut(BaseModel):
    day: date
    humid_hours: int
    rh_max: float
    t_min: float
    t_max: float
    precip_mm: float
    rain_prob_max: Optional[int] = None
    wind_max: Optional[float] = None


class SprayWindowOut(BaseModel):
    start: datetime
    end: datetime


class RadarAlertOut(BaseModel):
    crop_code: str
    disease: str
    level: Literal["low", "medium", "high"]
    score: float
    cases: int
    message: str
    spray_before: Optional[date] = None


class GridCellOut(BaseModel):
    lat: float
    lng: float
    cases: int
    top_disease: str


class RadarResponse(BaseModel):
    radius_km: float
    lookback_days: int
    total_cases: int
    weather: Optional[list[DayWeatherOut]] = None     # up to 7 days; the first 3 drive the risk score
    recent_rain_mm: Optional[float] = None             # rain over the last 3 days
    spray_windows: list[SprayWindowOut] = []           # good spraying times in the next 48 h
    alerts: list[RadarAlertOut] = []
    grid: list[GridCellOut] = []

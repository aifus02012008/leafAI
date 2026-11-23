from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel


class DayWeatherOut(BaseModel):
    day: date
    humid_hours: int
    rh_max: float
    t_min: float
    t_max: float
    precip_mm: float


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
    weather: Optional[list[DayWeatherOut]] = None
    alerts: list[RadarAlertOut] = []
    grid: list[GridCellOut] = []

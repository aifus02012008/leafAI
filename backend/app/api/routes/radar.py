from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.dependencies import optional_crop_filter
from app.core.crops import CropConfig
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.radar import DayWeatherOut, GridCellOut, RadarAlertOut, RadarResponse, SprayWindowOut
from app.services import radar_service, weather_service

router = APIRouter(prefix="/api/radar", tags=["Disease Radar"])


@router.get("", response_model=RadarResponse)
async def radar(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(5, gt=0, le=50),
    crop: CropConfig | None = Depends(optional_crop_filter),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cảnh báo sớm: ca bệnh đã chia sẻ quanh vị trí + dự báo thời tiết 7 ngày, mưa 3 ngày qua, giờ phun tốt."""
    crop_code = crop.code if crop else None
    cases = radar_service.nearby_cases(db, lat, lng, radius_km, crop_code)
    forecast = await run_in_threadpool(weather_service.get_forecast, lat, lng)
    alerts = radar_service.risk_alerts(
        cases,
        forecast.risk_days if forecast else None,
        radius_km,
        date.today(),
        forecast.recent_rain_mm if forecast else None,
    )
    grid = radar_service.case_grid(db, lat, lng, radius_km, crop_code)
    return RadarResponse(
        radius_km=radius_km,
        lookback_days=radar_service.LOOKBACK_DAYS,
        total_cases=sum(c.cases for c in cases),
        weather=[DayWeatherOut(**d.__dict__) for d in forecast.days] if forecast else None,
        recent_rain_mm=forecast.recent_rain_mm if forecast else None,
        spray_windows=[SprayWindowOut(start=w.start, end=w.end) for w in forecast.spray_windows] if forecast else [],
        alerts=[RadarAlertOut(**a.__dict__) for a in alerts],
        grid=[GridCellOut(**g.__dict__) for g in grid],
    )

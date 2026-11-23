"""Disease radar queries: nearby shared cases, risk alerts and an anonymised case grid."""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.api.presenters import display_label
from app.models.diagnosis import DiagnosisHistory
from app.services.geo import bounding_box, haversine_km
from app.services.radar_rules import DayWeather, NearbyCases, RiskAlert, assess_risk

LOOKBACK_DAYS = 7
RECENCY_HALF_LIFE_DAYS = 3.0
MIN_USERS_PER_CELL = 2      # k-anonymity: hide grid cells reported by fewer users
CELL_DEG = 0.02             # ~2 km grid cells on the map
LOCATION_DECIMALS = 3       # ~110 m: precision kept when storing a location


@dataclass(frozen=True)
class GridCell:
    lat: float
    lng: float
    cases: int
    top_disease: str


def coarsen(value: float | None) -> float | None:
    return None if value is None else round(value, LOCATION_DECIMALS)


def _recent_shared(db: Session, lat: float, lng: float, radius_km: float, crop_code: str | None):
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=LOOKBACK_DAYS)
    lat_min, lat_max, lng_min, lng_max = bounding_box(lat, lng, radius_km)
    q = db.query(DiagnosisHistory).filter(
        DiagnosisHistory.share_to_radar.is_(True),
        DiagnosisHistory.status == "detected",
        DiagnosisHistory.created_at >= since,
        DiagnosisHistory.latitude.between(lat_min, lat_max),
        DiagnosisHistory.longitude.between(lng_min, lng_max),
    )
    if crop_code:
        q = q.filter(DiagnosisHistory.crop_code == crop_code)
    return [
        r for r in q.all()
        if r.detections and haversine_km(lat, lng, r.latitude, r.longitude) <= radius_km
    ]


def _top_label(rec: DiagnosisHistory) -> str:
    best = max(rec.detections, key=lambda d: d.confidence)
    return display_label(rec, best.class_name)


def _weight(rec: DiagnosisHistory, now: datetime) -> float:
    age_days = max((now - rec.created_at).total_seconds() / 86400, 0.0)
    best = max(d.confidence for d in rec.detections)
    return best * math.exp(-age_days * math.log(2) / RECENCY_HALF_LIFE_DAYS)


def nearby_cases(db: Session, lat: float, lng: float, radius_km: float, crop_code: str | None) -> list[NearbyCases]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    groups: dict[tuple[str, str], list[DiagnosisHistory]] = defaultdict(list)
    for rec in _recent_shared(db, lat, lng, radius_km, crop_code):
        groups[(rec.crop_code, _top_label(rec))].append(rec)
    result = [
        NearbyCases(
            crop_code=crop,
            disease=disease,
            cases=len(recs),
            distinct_users=len({r.user_id for r in recs}),
            weighted=round(sum(_weight(r, now) for r in recs), 3),
        )
        for (crop, disease), recs in groups.items()
    ]
    return sorted(result, key=lambda c: c.weighted, reverse=True)


def risk_alerts(
    cases: list[NearbyCases], outlook: list[DayWeather] | None, radius_km: float, today: date
) -> list[RiskAlert]:
    order = {"high": 0, "medium": 1, "low": 2}
    alerts = [assess_risk(c, outlook, radius_km, today) for c in cases]
    return sorted(alerts, key=lambda a: (order[a.level], -a.cases))


def case_grid(db: Session, lat: float, lng: float, radius_km: float, crop_code: str | None) -> list[GridCell]:
    cells: dict[tuple[float, float], list[DiagnosisHistory]] = defaultdict(list)
    for rec in _recent_shared(db, lat, lng, radius_km, crop_code):
        key = (round(rec.latitude / CELL_DEG) * CELL_DEG, round(rec.longitude / CELL_DEG) * CELL_DEG)
        cells[key].append(rec)
    grid = []
    for (clat, clng), recs in cells.items():
        if len({r.user_id for r in recs}) < MIN_USERS_PER_CELL:
            continue
        labels: dict[str, int] = defaultdict(int)
        for r in recs:
            labels[_top_label(r)] += 1
        grid.append(GridCell(round(clat, 4), round(clng, 4), len(recs), max(labels, key=labels.get)))
    return grid

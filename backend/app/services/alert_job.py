"""Periodic job: radar alerts for watched farms and follow-up photo reminders, then push delivery."""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.crops import CropNotFoundError, get_crop
from app.models.treatment import Treatment
from app.models.watched_farm import WatchedFarm
from app.services import push_service, weather_service
from app.services.notification_service import create_notification
from app.services.radar_service import nearby_cases, risk_alerts

logger = logging.getLogger(__name__)

ALERT_LEVELS = ("high",)
VIETNAM_TZ = timezone(timedelta(hours=7))  # Vietnam has no daylight saving time


def vietnam_today(now: datetime | None = None) -> date:
    """Calendar date in Vietnam (servers usually run on UTC)."""
    return (now or datetime.now(timezone.utc)).astimezone(VIETNAM_TZ).date()


@dataclass(frozen=True)
class JobReport:
    farms_checked: int
    radar_created: int
    followup_created: int
    pushed: int


def _crop_name(code: str) -> str:
    try:
        return get_crop(code).name_vi
    except CropNotFoundError:
        return code


def _radar_key(farm: WatchedFarm, crop_code: str, disease: str, today: date) -> str:
    year, week, _ = today.isocalendar()
    digest = hashlib.sha1(disease.encode("utf-8")).hexdigest()[:12]
    return f"radar:{farm.id}:{crop_code}:{digest}:{year}-W{week:02d}"


def _check_farm(db: Session, farm: WatchedFarm, today: date) -> int:
    cases = nearby_cases(db, farm.latitude, farm.longitude, farm.radius_km, farm.crop_code)
    if not cases:
        return 0
    outlook = weather_service.get_outlook(farm.latitude, farm.longitude)
    created = 0
    for alert in risk_alerts(cases, outlook, farm.radius_km, today):
        if alert.level not in ALERT_LEVELS:
            continue
        note = create_notification(
            db,
            user_id=farm.user_id,
            kind="radar",
            title=f"Nguy cơ cao quanh {farm.name}: {_crop_name(alert.crop_code)}",
            body=alert.message,
            link="/radar",
            dedupe_key=_radar_key(farm, alert.crop_code, alert.disease, today),
        )
        created += note is not None
    return created


def _followup_reminders(db: Session, today: date) -> int:
    due = (
        db.query(Treatment)
        .filter(Treatment.status == "awaiting_followup", Treatment.followup_due_on <= today)
        .all()
    )
    created = 0
    for tr in due:
        note = create_notification(
            db,
            user_id=tr.user_id,
            kind="followup",
            title=f"Đến hạn chụp lại lá {_crop_name(tr.crop_code).lower()}",
            body="Hãy chụp lại chiếc lá đã phun thuốc để LEAF AI đánh giá thuốc có tác dụng hay không.",
            link=f"/diagnose?followup={tr.id}&crop={tr.crop_code}",
            dedupe_key=f"followup:{tr.id}",
        )
        created += note is not None
    return created


def _run_stage(name: str, fn, db: Session) -> int:
    """Run one job stage; a failure is logged and isolated so later stages still run."""
    try:
        return fn()
    except Exception:
        db.rollback()
        logger.exception("Alert job stage failed: %s", name)
        return 0


def run_alert_job(db: Session, today: date) -> JobReport:
    farms = db.query(WatchedFarm).filter(WatchedFarm.alerts_enabled.is_(True)).all()
    radar = 0
    for farm in farms:
        try:
            radar += _check_farm(db, farm, today)
        except Exception:  # one bad farm must not stop the whole run
            db.rollback()
            logger.exception("Radar check failed for farm %s", farm.id)
    followups = _run_stage("follow-up reminders", lambda: _followup_reminders(db, today), db)
    pushed = _run_stage("push delivery", lambda: push_service.deliver_pending(db), db)
    report = JobReport(farms_checked=len(farms), radar_created=radar, followup_created=followups, pushed=pushed)
    logger.info("Alert job finished: %s", report)
    return report

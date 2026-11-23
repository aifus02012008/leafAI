"""Internal endpoints triggered by the scheduler (GitHub Actions cron)."""
from __future__ import annotations

import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.farm import AlertJobReport
from app.services import alert_job

router = APIRouter(prefix="/api/internal", tags=["Internal"], include_in_schema=False)


def require_cron_secret(x_cron_secret: str | None = Header(default=None)) -> None:
    if not settings.CRON_SECRET:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Scheduler is not configured.")
    if not x_cron_secret or not hmac.compare_digest(x_cron_secret.encode(), settings.CRON_SECRET.encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid scheduler secret.")


@router.post("/jobs/alerts", response_model=AlertJobReport, dependencies=[Depends(require_cron_secret)])
async def run_alerts(db: Session = Depends(get_db)):
    report = await run_in_threadpool(alert_job.run_alert_job, db, alert_job.vietnam_today())
    return AlertJobReport(**report.__dict__)

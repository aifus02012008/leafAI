"""Periodic alert job: radar alerts for watched farms, follow-up reminders, push delivery, cron auth."""
from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.init_db import init_database
from app.db.session import SessionLocal
from app.main import app
from app.models.detection import DetectionResult
from app.models.diagnosis import DiagnosisHistory
from app.models.notification import Notification, PushSubscription
from app.models.treatment import Treatment
from app.models.watched_farm import WatchedFarm
from app.services import alert_job, push_service, weather_service
from app.services.radar_rules import DayWeather
from app.tests.helpers import register, user_id

FARM = (9.9001, 105.7002)   # isolated spot used only by these tests
DISEASE = "Cháy lá do Phytophthora trên sầu riêng (Durian Phytophthora leaf blight)"


@pytest.fixture(scope="module", autouse=True)
def _db():
    init_database()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def humid(monkeypatch):
    today = date.today()
    days = [DayWeather(today + timedelta(days=i + 1), 14, 97, 23, 30, 12.0) for i in range(3)]
    monkeypatch.setattr(weather_service, "get_outlook", lambda lat, lng: days)


@pytest.fixture
def sent(monkeypatch):
    calls = []
    monkeypatch.setattr(push_service, "send_push", lambda sub, payload: calls.append((sub.endpoint, payload)) or push_service.SENT)
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "pub")
    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "priv")
    return calls


def _clean_area():
    db = SessionLocal()
    try:
        db.query(DiagnosisHistory).filter(DiagnosisHistory.latitude.between(FARM[0] - 0.2, FARM[0] + 0.2)).delete(
            synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _seed_cases(n: int):
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for i in range(n):
            uid = user_id(register_cache[i % len(register_cache)])
            rec = DiagnosisHistory(user_id=uid, crop_code="durian", original_image_path="originals/x.jpg",
                                   status="detected", latitude=FARM[0] + 0.001 * i, longitude=FARM[1],
                                   share_to_radar=True, created_at=now - timedelta(hours=i))
            db.add(rec)
            db.flush()
            db.add(DetectionResult(history_id=rec.id, class_name=DISEASE, confidence=0.9, x1=0, y1=0, x2=1, y2=1))
        db.commit()
    finally:
        db.close()


register_cache: list[str] = []


def _farm(email: str, alerts=True) -> int:
    db = SessionLocal()
    try:
        f = WatchedFarm(user_id=user_id(email), name="Vườn", latitude=FARM[0], longitude=FARM[1],
                        radius_km=5, crop_code="durian", alerts_enabled=alerts)
        db.add(f)
        db.commit()
        return f.id
    finally:
        db.close()


def _subscribe(email: str):
    db = SessionLocal()
    try:
        db.add(PushSubscription(user_id=user_id(email), endpoint=f"https://fcm.googleapis.com/fcm/send/{email}",
                                p256dh="k", auth="a"))
        db.commit()
    finally:
        db.close()


def _notifications(email: str) -> list[Notification]:
    db = SessionLocal()
    try:
        return db.query(Notification).filter(Notification.user_id == user_id(email)).all()
    finally:
        db.close()


def test_high_risk_creates_one_radar_notification_and_push(client, humid, sent):
    _clean_area()
    register_cache[:] = []
    for i in range(4):
        email = f"job_reporter{i}@leafai.dev"
        register(client, email)
        register_cache.append(email)
    _seed_cases(10)
    owner = "job_owner@leafai.dev"
    register(client, owner)
    _farm(owner)
    _subscribe(owner)

    db = SessionLocal()
    try:
        report = alert_job.run_alert_job(db, today=date.today())
    finally:
        db.close()
    assert report.radar_created >= 1
    notes = [n for n in _notifications(owner) if n.kind == "radar"]
    assert len(notes) == 1
    assert "Phytophthora" in notes[0].body and notes[0].pushed_at is not None
    assert any(ep.endswith(owner) for ep, _ in sent)

    db = SessionLocal()
    try:
        alert_job.run_alert_job(db, today=date.today())   # second run the same week: no duplicate
    finally:
        db.close()
    assert len([n for n in _notifications(owner) if n.kind == "radar"]) == 1


def test_disabled_farm_gets_no_alert(client, humid, sent):
    owner = "job_disabled@leafai.dev"
    register(client, owner)
    _farm(owner, alerts=False)
    db = SessionLocal()
    try:
        alert_job.run_alert_job(db, today=date.today())
    finally:
        db.close()
    assert _notifications(owner) == []


def test_followup_reminder_when_due(client, humid, sent):
    owner = "job_followup@leafai.dev"
    register(client, owner)
    db = SessionLocal()
    try:
        uid = user_id(owner)
        diag = DiagnosisHistory(user_id=uid, crop_code="tea", original_image_path="originals/y.jpg", status="detected")
        db.add(diag)
        db.flush()
        tr = Treatment(user_id=uid, diagnosis_id=diag.id, crop_code="tea", active_code="mancozeb",
                       applied_on=date.today() - timedelta(days=5), followup_due_on=date.today() - timedelta(days=1),
                       status="awaiting_followup")
        db.add(tr)
        db.commit()
        tr_id = tr.id
        alert_job.run_alert_job(db, today=date.today())
        alert_job.run_alert_job(db, today=date.today())
    finally:
        db.close()
    reminders = [n for n in _notifications(owner) if n.kind == "followup"]
    assert len(reminders) == 1
    assert f"followup={tr_id}" in reminders[0].link


def test_dead_push_subscription_is_removed(client, humid, monkeypatch):
    owner = "job_dead_sub@leafai.dev"
    register(client, owner)
    _subscribe(owner)
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "pub")
    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "priv")
    monkeypatch.setattr(push_service, "send_push", lambda sub, payload: push_service.GONE)
    db = SessionLocal()
    try:
        n = Notification(user_id=user_id(owner), kind="radar", title="t", body="b", dedupe_key="dead-sub-test")
        db.add(n)
        db.commit()
        push_service.deliver_pending(db)
        left = db.query(PushSubscription).filter(PushSubscription.user_id == user_id(owner)).count()
    finally:
        db.close()
    assert left == 0


# ---------- cron endpoint ----------

def test_cron_endpoint_requires_configured_secret(client, monkeypatch):
    monkeypatch.setattr(settings, "CRON_SECRET", None)
    assert client.post("/api/internal/jobs/alerts", headers={"X-Cron-Secret": "x"}).status_code == 503


def test_cron_endpoint_rejects_wrong_secret(client, monkeypatch):
    monkeypatch.setattr(settings, "CRON_SECRET", "s" * 32)
    assert client.post("/api/internal/jobs/alerts").status_code == 401
    assert client.post("/api/internal/jobs/alerts", headers={"X-Cron-Secret": "wrong"}).status_code == 401


def test_cron_endpoint_runs_job(client, monkeypatch, humid):
    monkeypatch.setattr(settings, "CRON_SECRET", "s" * 32)
    res = client.post("/api/internal/jobs/alerts", headers={"X-Cron-Secret": "s" * 32})
    assert res.status_code == 200
    assert {"farms_checked", "radar_created", "followup_created", "pushed"} <= set(res.json())

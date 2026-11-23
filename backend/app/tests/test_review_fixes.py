"""Regression tests for code/security review findings."""
from datetime import date, datetime, timedelta, timezone
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core import rate_limit
from app.core.config import settings
from app.db.init_db import init_database
from app.db.session import SessionLocal
from app.main import app
from app.models.notification import Notification, PushSubscription
from app.services import alert_job, prediction_service, push_service
from app.services.storage import SIGNED_URL_TTL_SECONDS, StorageError
from app.tests.helpers import jpeg, register, user_id

FCM = "https://fcm.googleapis.com/fcm/send/"


@pytest.fixture(scope="module", autouse=True)
def _db():
    init_database()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ---------- storage failures must not break diagnosis ----------

def test_prediction_survives_remote_storage_failure(client, monkeypatch):
    class Broken:
        def save(self, key, path):
            raise StorageError("supabase down")

    monkeypatch.setattr(prediction_service, "get_storage", lambda: Broken())
    h = register(client, "storage_down@leafai.dev")
    res = client.post("/api/predict", headers=h, files={"file": ("a.jpg", jpeg(), "image/jpeg")})
    assert res.status_code == 200, res.text


def test_prediction_survives_misconfigured_storage(client, monkeypatch):
    def boom():
        raise StorageError("missing credentials")

    monkeypatch.setattr(prediction_service, "get_storage", boom)
    h = register(client, "storage_misconfig@leafai.dev")
    assert client.post("/api/predict", headers=h, files={"file": ("a.jpg", jpeg(), "image/jpeg")}).status_code == 200


def test_signed_urls_are_short_lived():
    assert SIGNED_URL_TTL_SECONDS <= 300


# ---------- EXIF / GPS stripping ----------

def _jpeg_with_gps() -> BytesIO:
    img = Image.new("RGB", (64, 64), (60, 140, 60))
    exif = Image.Exif()
    exif[0x8825] = {1: "N", 2: (10.0, 14.0, 24.0), 3: "E", 4: (106.0, 22.0, 32.0)}  # GPSInfo
    exif[0x010F] = "PhoneMaker"
    buf = BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    buf.seek(0)
    return buf


def test_uploaded_photo_metadata_is_stripped(client):
    h = register(client, "exif_user@leafai.dev")
    res = client.post("/api/predict", headers=h, files={"file": ("gps.jpg", _jpeg_with_gps(), "image/jpeg")})
    assert res.status_code == 200
    stored = settings.storage_dir / res.json()["original_image_url"].replace("/api/images/", "")
    with Image.open(stored) as im:
        exif = im.getexif()
        assert 0x8825 not in exif and not exif.get_ifd(0x8825)
        assert 0x010F not in exif


# ---------- push delivery robustness ----------

def _sub(email: str, endpoint_suffix: str) -> None:
    db = SessionLocal()
    try:
        db.add(PushSubscription(user_id=user_id(email), endpoint=FCM + endpoint_suffix, p256dh="k", auth="a"))
        db.commit()
    finally:
        db.close()


def _note(email: str, key: str, age: timedelta = timedelta(0)) -> int:
    db = SessionLocal()
    try:
        n = Notification(user_id=user_id(email), kind="radar", title="t", body="b", dedupe_key=key,
                         created_at=datetime.now(timezone.utc).replace(tzinfo=None) - age)
        db.add(n)
        db.commit()
        return n.id
    finally:
        db.close()


@pytest.fixture
def vapid(monkeypatch):
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", "pub")
    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", "priv")


def test_send_push_network_error_is_reported_as_failed(monkeypatch):
    import pywebpush
    import requests

    def boom(**kw):
        raise requests.ConnectionError("network down")

    monkeypatch.setattr(pywebpush, "webpush", boom)
    sub = PushSubscription(endpoint=FCM + "x", p256dh="k", auth="a")
    assert push_service.send_push(sub, {"title": "t"}) == push_service.FAILED


def test_old_notifications_are_not_pushed(client, vapid, monkeypatch):
    email = "push_old@leafai.dev"
    register(client, email)
    _sub(email, "old-user")
    sent = []
    monkeypatch.setattr(push_service, "send_push", lambda sub, payload: sent.append(payload) or push_service.SENT)
    _note(email, "old-one", age=timedelta(days=3))
    fresh = _note(email, "fresh-one")
    db = SessionLocal()
    try:
        push_service.deliver_pending(db)
        assert [p["tag"] for p in sent] == [f"leafai-radar-{fresh}"]
        pending = db.query(Notification).filter(Notification.user_id == user_id(email), Notification.pushed_at.is_(None)).count()
        assert pending == 0
        sent.clear()
        push_service.deliver_pending(db)  # nothing left to send twice
        assert sent == []
    finally:
        db.close()


def test_alert_job_survives_push_stage_crash(client, monkeypatch):
    def boom(db):
        raise RuntimeError("push backend exploded")

    monkeypatch.setattr(push_service, "deliver_pending", boom)
    db = SessionLocal()
    try:
        report = alert_job.run_alert_job(db, today=date.today())
    finally:
        db.close()
    assert report.pushed == 0


def test_vietnam_today_uses_utc_plus_7():
    late_utc = datetime(2026, 11, 23, 18, 30, tzinfo=timezone.utc)  # 01:30 on 24/11 in Vietnam
    assert alert_job.vietnam_today(late_utc) == date(2026, 11, 24)


# ---------- push subscription takeover ----------

KEYS_A = {"p256dh": "A" * 87, "auth": "a" * 22}
KEYS_B = {"p256dh": "B" * 87, "auth": "b" * 22}


def test_push_endpoint_cannot_be_hijacked_with_different_keys(client):
    victim = register(client, "push_victim@leafai.dev")
    attacker = register(client, "push_attacker@leafai.dev")
    ep = FCM + "victim-device"
    assert client.post("/api/push/subscriptions", headers=victim, json={"endpoint": ep, "keys": KEYS_A}).status_code == 201
    assert client.post("/api/push/subscriptions", headers=attacker, json={"endpoint": ep, "keys": KEYS_B}).status_code == 409


def test_same_browser_can_switch_account(client):
    first = register(client, "push_switch1@leafai.dev")
    second = register(client, "push_switch2@leafai.dev")
    ep = FCM + "shared-browser"
    assert client.post("/api/push/subscriptions", headers=first, json={"endpoint": ep, "keys": KEYS_A}).status_code == 201
    assert client.post("/api/push/subscriptions", headers=second, json={"endpoint": ep, "keys": KEYS_A}).status_code == 201


# ---------- rate limiting ----------

class _Req:
    def __init__(self, xff: str | None, host: str = "10.0.0.1"):
        self.headers = {"x-forwarded-for": xff} if xff else {}
        self.client = type("C", (), {"host": host})()


def test_proxy_ip_uses_rightmost_forwarded_entry(monkeypatch):
    monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", True)
    assert rate_limit.client_ip(_Req("1.2.3.4, 203.0.113.9")) == "203.0.113.9"
    monkeypatch.setattr(settings, "TRUST_PROXY_HEADERS", False)
    assert rate_limit.client_ip(_Req("1.2.3.4, 203.0.113.9")) == "10.0.0.1"


def test_login_is_limited_per_email_even_across_ips(client, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "AUTH_RATE_LIMIT_PER_MINUTE", 100)
    monkeypatch.setattr(settings, "LOGIN_PER_EMAIL_PER_MINUTE", 2)
    body = {"email": "target_account@leafai.dev", "password": "Wrong123!"}
    codes = [client.post("/api/auth/login", json=body).status_code for _ in range(3)]
    assert codes == [401, 401, 429]


def test_rate_limiter_memory_is_bounded(monkeypatch):
    monkeypatch.setattr(rate_limit, "_MAX_TRACKED_KEYS", 100)
    rate_limit.reset_rate_limits()
    for i in range(500):
        rate_limit.hit(f"k{i}", 5)
    assert len(rate_limit._hits) <= 100


def test_image_redirects_are_rate_limited(client, monkeypatch):
    from app.services import storage

    class Remote:
        def signed_url(self, key):
            return f"https://cdn.example/{key}"

    monkeypatch.setattr(storage, "get_storage", lambda: Remote())
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "IMAGE_REDIRECT_PER_MINUTE", 2)
    codes = [client.get(f"/api/images/originals/missing{i}_orig.jpg", follow_redirects=False).status_code for i in range(3)]
    assert codes == [307, 307, 429]


# ---------- headers ----------

def test_api_responses_have_restrictive_csp(client):
    csp = client.get("/api/health").headers["Content-Security-Policy"]
    assert "default-src 'none'" in csp and "frame-ancestors 'none'" in csp

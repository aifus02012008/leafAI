"""Watched farms, in-app notifications, push subscriptions and location privacy."""
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.init_db import init_database
from app.db.session import SessionLocal
from app.main import app
from app.models.diagnosis import DiagnosisHistory
from app.models.notification import Notification
from app.tests.helpers import jpeg, register, user_id

FCM = "https://fcm.googleapis.com/fcm/send/abc123"
KEYS = {"p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUls0VJXg7A8u-Ts1XbjhazAkj7I99e8QcYP7DkM", "auth": "tBHItJI5svbpez7KI4CCXg"}


@pytest.fixture(scope="module", autouse=True)
def _db():
    init_database()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ---------- farms ----------

def test_farm_crud_and_coarsened_location(client):
    h = register(client, "farm_owner@leafai.dev")
    res = client.post("/api/farms", headers=h, json={
        "name": "Vườn nhà", "latitude": 10.123456, "longitude": 106.654321, "radius_km": 5, "crop_code": "durian",
    })
    assert res.status_code == 201, res.text
    farm = res.json()
    assert (farm["latitude"], farm["longitude"]) == (10.123, 106.654)
    assert farm["alerts_enabled"] is True

    assert [f["id"] for f in client.get("/api/farms", headers=h).json()] == [farm["id"]]

    upd = client.patch(f"/api/farms/{farm['id']}", headers=h, json={"alerts_enabled": False})
    assert upd.status_code == 200 and upd.json()["alerts_enabled"] is False

    assert client.delete(f"/api/farms/{farm['id']}", headers=h).status_code == 200
    assert client.get("/api/farms", headers=h).json() == []


@pytest.mark.parametrize("payload", [
    {"name": "", "latitude": 10, "longitude": 106},
    {"name": "x", "latitude": 91, "longitude": 106},
    {"name": "x", "latitude": 10, "longitude": 106, "radius_km": 0},
    {"name": "x", "latitude": 10, "longitude": 106, "radius_km": 100},
    {"name": "x", "latitude": 10, "longitude": 106, "crop_code": "banana"},
])
def test_farm_validation(client, payload):
    h = register(client, "farm_validation@leafai.dev")
    assert client.post("/api/farms", headers=h, json=payload).status_code == 422


def test_farm_limit_per_user(client, monkeypatch):
    monkeypatch.setattr(settings, "MAX_FARMS_PER_USER", 2)
    h = register(client, "farm_limit@leafai.dev")
    for i in range(2):
        assert client.post("/api/farms", headers=h, json={"name": f"V{i}", "latitude": 10, "longitude": 106}).status_code == 201
    assert client.post("/api/farms", headers=h, json={"name": "V3", "latitude": 10, "longitude": 106}).status_code == 422


def test_farm_ownership(client):
    owner = register(client, "farm_a@leafai.dev")
    other = register(client, "farm_b@leafai.dev")
    fid = client.post("/api/farms", headers=owner, json={"name": "A", "latitude": 10, "longitude": 106}).json()["id"]
    assert client.patch(f"/api/farms/{fid}", headers=other, json={"alerts_enabled": False}).status_code == 404
    assert client.delete(f"/api/farms/{fid}", headers=other).status_code == 404
    assert client.get("/api/farms", headers=other).json() == []


def test_farms_require_auth(client):
    assert client.get("/api/farms").status_code == 401


# ---------- notifications ----------

def _notify(email: str, key: str, title: str = "Cảnh báo") -> int:
    db = SessionLocal()
    try:
        n = Notification(user_id=user_id(email), kind="radar", title=title, body="Nội dung", link="/radar", dedupe_key=key)
        db.add(n)
        db.commit()
        return n.id
    finally:
        db.close()


def test_notifications_list_and_read(client):
    h = register(client, "notif_user@leafai.dev")
    n1 = _notify("notif_user@leafai.dev", "k1")
    _notify("notif_user@leafai.dev", "k2")
    body = client.get("/api/notifications", headers=h).json()
    assert body["unread_count"] == 2 and len(body["items"]) == 2

    assert client.post(f"/api/notifications/{n1}/read", headers=h).status_code == 200
    assert client.get("/api/notifications", headers=h).json()["unread_count"] == 1
    assert client.post("/api/notifications/read-all", headers=h).status_code == 200
    assert client.get("/api/notifications", headers=h).json()["unread_count"] == 0


def test_notifications_are_private(client):
    register(client, "notif_owner@leafai.dev")
    intruder = register(client, "notif_intruder@leafai.dev")
    nid = _notify("notif_owner@leafai.dev", "private")
    assert client.post(f"/api/notifications/{nid}/read", headers=intruder).status_code == 404
    assert client.get("/api/notifications", headers=intruder).json()["items"] == []


# ---------- push subscriptions ----------

def test_push_config_reports_disabled_without_vapid(client, monkeypatch):
    monkeypatch.setattr(settings, "VAPID_PUBLIC_KEY", None)
    monkeypatch.setattr(settings, "VAPID_PRIVATE_KEY", None)
    assert client.get("/api/push/config").json() == {"enabled": False, "public_key": None}


def test_push_subscribe_and_unsubscribe(client):
    h = register(client, "push_user@leafai.dev")
    sub = {"endpoint": FCM, "keys": KEYS}
    assert client.post("/api/push/subscriptions", headers=h, json=sub).status_code == 201
    assert client.post("/api/push/subscriptions", headers=h, json=sub).status_code == 201  # idempotent
    res = client.request("DELETE", "/api/push/subscriptions", headers=h, json={"endpoint": FCM})
    assert res.status_code == 200 and res.json()["removed"] == 1


@pytest.mark.parametrize("endpoint", [
    "http://fcm.googleapis.com/fcm/send/x",          # not https
    "https://127.0.0.1/push",                         # SSRF: internal host
    "https://evil.example.com/push",                  # not a known push service
    "https://fcm.googleapis.com.evil.com/x",          # suffix trick
])
def test_push_endpoint_must_be_known_push_service(client, endpoint):
    h = register(client, "push_ssrf@leafai.dev")
    assert client.post("/api/push/subscriptions", headers=h, json={"endpoint": endpoint, "keys": KEYS}).status_code == 422


# ---------- privacy ----------

def test_purge_location_data(client):
    h = register(client, "privacy_user@leafai.dev")
    data = {"crop": "tea", "latitude": "10.5", "longitude": "106.5", "share_to_radar": "true"}
    diag_id = client.post("/api/predict", headers=h, data=data, files={"file": ("a.jpg", jpeg(), "image/jpeg")}).json()["id"]
    client.post("/api/farms", headers=h, json={"name": "V", "latitude": 10, "longitude": 106})

    res = client.delete("/api/privacy/location", headers=h)
    assert res.status_code == 200
    assert res.json() == {"diagnoses_cleared": 1, "farms_deleted": 1}

    db = SessionLocal()
    try:
        rec = db.get(DiagnosisHistory, diag_id)
        assert (rec.latitude, rec.longitude, rec.share_to_radar) == (None, None, False)
    finally:
        db.close()
    assert client.get("/api/farms", headers=h).json() == []

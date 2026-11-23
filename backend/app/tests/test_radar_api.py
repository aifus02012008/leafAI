"""Integration tests for the disease radar: opt-in location, nearby alerts, weather, anonymised grid."""
from datetime import date, timedelta
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.db.init_db import init_database
from app.db.session import SessionLocal
from app.main import app
from app.models.diagnosis import DiagnosisHistory
from app.models.user import User
from app.services import weather_service
from app.services.detection_rules import RawDetection
from app.services.model_registry import model_registry
from app.services.radar_rules import DayWeather

# A spot in the Mekong Delta far from any other test data.
LAT, LNG = 10.2401, 106.3756


class _Durian:
    version = "durian-test"
    class_names = {0: "Leaf_Phytophthora"}

    def detect(self, image_path):
        return [RawDetection("Leaf_Phytophthora", 0.9, 10, 10, 100, 100)]


@pytest.fixture(scope="module", autouse=True)
def _setup():
    init_database()
    model_registry.register("durian", _Durian())
    yield
    model_registry.unregister("durian")


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def humid_weather(monkeypatch):
    today = date.today()
    days = [DayWeather(today + timedelta(days=i + 1), 14, 97, 23, 30, 12.0) for i in range(3)]
    monkeypatch.setattr(weather_service, "get_outlook", lambda lat, lng: days)
    return days


def _auth(client, email):
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        if u:
            db.delete(u)
            db.commit()
    finally:
        db.close()
    pw = "Password123!"
    res = client.post("/api/auth/register", json={"email": email, "password": pw, "password_confirmation": pw})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _report(client, headers, lat, lng, share=True) -> dict:
    buf = BytesIO()
    Image.new("RGB", (64, 64), (60, 140, 60)).save(buf, format="JPEG")
    buf.seek(0)
    data = {"crop": "durian", "latitude": str(lat), "longitude": str(lng), "share_to_radar": "true" if share else "false"}
    res = client.post("/api/predict", headers=headers, data=data, files={"file": ("a.jpg", buf, "image/jpeg")})
    assert res.status_code == 200, res.text
    return res.json()


def test_location_stored_only_with_consent_and_coarsened(client):
    headers = _auth(client, "radar_consent@leafai.dev")
    shared = _report(client, headers, 10.123456789, 106.987654321, share=True)
    private = _report(client, headers, 10.5, 106.5, share=False)
    db = SessionLocal()
    try:
        s = db.get(DiagnosisHistory, shared["id"])
        p = db.get(DiagnosisHistory, private["id"])
        assert (s.latitude, s.longitude, s.share_to_radar) == (10.123, 106.988, True)
        assert (p.latitude, p.longitude, p.share_to_radar) == (None, None, False)
    finally:
        db.close()


def test_radar_alerts_nearby_cases_with_weather(client, humid_weather):
    reporters = [_auth(client, f"radar_farmer{i}@leafai.dev") for i in range(4)]
    for i, h in enumerate(reporters):
        _report(client, h, LAT + 0.001 * i, LNG + 0.001 * i)
    _report(client, reporters[0], LAT + 0.5, LNG)  # ~55 km away: outside radius

    viewer = _auth(client, "radar_viewer@leafai.dev")
    res = client.get("/api/radar", headers=viewer, params={"lat": LAT, "lng": LNG, "radius_km": 5, "crop": "durian"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["total_cases"] == 4
    assert len(body["weather"]) == 3
    alert = body["alerts"][0]
    assert "Phytophthora" in alert["disease"]
    assert alert["level"] in ("medium", "high")
    assert "4 ca" in alert["message"]
    assert body["grid"] and all(c["cases"] >= 2 for c in body["grid"])


def test_grid_hides_cells_with_a_single_reporter(client, humid_weather):
    lone = _auth(client, "radar_lone@leafai.dev")
    _report(client, lone, 11.9, 108.4)
    viewer = _auth(client, "radar_viewer2@leafai.dev")
    body = client.get("/api/radar", headers=viewer, params={"lat": 11.9, "lng": 108.4}).json()
    assert body["total_cases"] >= 1
    assert body["grid"] == []


def test_radar_without_weather_still_answers(client, monkeypatch):
    monkeypatch.setattr(weather_service, "get_outlook", lambda lat, lng: None)
    viewer = _auth(client, "radar_noweather@leafai.dev")
    body = client.get("/api/radar", headers=viewer, params={"lat": 0.0, "lng": 0.0}).json()
    assert body["weather"] is None
    assert body["alerts"] == []


def test_radar_validation_and_auth(client):
    assert client.get("/api/radar", params={"lat": 10, "lng": 106}).status_code == 401
    viewer = _auth(client, "radar_validation@leafai.dev")
    assert client.get("/api/radar", headers=viewer, params={"lat": 100, "lng": 106}).status_code == 422
    assert client.get("/api/radar", headers=viewer, params={"lat": 10, "lng": 106, "radius_km": 500}).status_code == 422


def test_weather_parsing_groups_hours_by_day():
    payload = {"hourly": {
        "time": ["2026-11-26T00:00", "2026-11-26T01:00", "2026-11-27T00:00"],
        "relative_humidity_2m": [95, 80, 92],
        "temperature_2m": [22.0, 25.0, 21.0],
        "precipitation": [1.0, 0.5, 0.0],
    }}
    days = weather_service.parse_hourly(payload)
    assert [d.day.isoformat() for d in days] == ["2026-11-26", "2026-11-27"]
    assert days[0].humid_hours == 1 and days[0].precip_mm == 1.5 and days[0].t_max == 25.0


def test_weather_service_handles_errors(monkeypatch):
    import httpx

    weather_service.clear_cache()

    def boom(*a, **k):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(weather_service.httpx, "get", boom)
    assert weather_service.get_outlook(1.0, 2.0) is None

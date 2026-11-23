"""Integration tests for multi-crop support: crops, diseases, predict, history, feedback."""
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.crops import get_crop
from app.db.init_db import init_database
from app.db.session import SessionLocal
from app.main import app
from app.models.user import User
from app.services.detection_rules import RawDetection
from app.services.model_registry import model_registry


class FakeDetector:
    """Stand-in for a YOLO model so tests do not need real durian weights."""

    version = "durian-test"
    class_names = {0: "Leaf_Phytophthora", 1: "Healthy_leaf"}

    def detect(self, image_path: str) -> list[RawDetection]:
        return [RawDetection(label="Leaf_Phytophthora", confidence=0.91, x1=10, y1=10, x2=200, y2=220)]


@pytest.fixture(scope="module", autouse=True)
def _db():
    init_database()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def _auth_headers(client: TestClient, email: str) -> dict[str, str]:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            db.delete(existing)
            db.commit()
    finally:
        db.close()
    pw = "Password123!"
    res = client.post(
        "/api/auth/register",
        json={"email": email, "password": pw, "password_confirmation": pw},
    )
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _jpeg() -> BytesIO:
    buf = BytesIO()
    Image.new("RGB", (320, 320), color=(60, 140, 60)).save(buf, format="JPEG")
    buf.seek(0)
    return buf


@pytest.fixture
def fake_durian_model():
    model_registry.register("durian", FakeDetector())
    yield
    model_registry.unregister("durian")


# ---------- /api/crops ----------

def test_list_crops(client):
    res = client.get("/api/crops")
    assert res.status_code == 200
    crops = {c["code"]: c for c in res.json()}
    assert set(crops) == {"tea", "durian", "mangosteen", "rambutan"}
    assert crops["tea"]["is_available"] is True
    assert crops["tea"]["name_vi"]
    assert crops["durian"]["disease_count"] >= 1


def test_crop_availability_reflects_registered_model(client, fake_durian_model):
    crops = {c["code"]: c for c in client.get("/api/crops").json()}
    assert crops["durian"]["is_available"] is True


# ---------- /api/diseases ----------

def test_diseases_filtered_by_crop(client):
    tea = client.get("/api/diseases", params={"crop": "tea"}).json()
    durian = client.get("/api/diseases", params={"crop": "durian"}).json()
    assert len(tea) == 6
    assert all(d["crop_code"] == "tea" for d in tea)
    assert len(durian) >= 1
    assert all(d["crop_code"] == "durian" for d in durian)


def test_diseases_without_filter_returns_all_crops(client):
    all_items = client.get("/api/diseases").json()
    assert {d["crop_code"] for d in all_items} == {"tea", "durian", "mangosteen", "rambutan"}


def test_diseases_unknown_crop_is_rejected(client):
    assert client.get("/api/diseases", params={"crop": "banana"}).status_code == 422


# ---------- /api/predict ----------

def test_predict_defaults_to_tea(client):
    headers = _auth_headers(client, "mc_default@leafai.dev")
    res = client.post("/api/predict", headers=headers, files={"file": ("a.jpg", _jpeg(), "image/jpeg")})
    assert res.status_code == 200, res.text
    assert res.json()["crop_code"] == "tea"


def test_predict_unknown_crop_rejected(client):
    headers = _auth_headers(client, "mc_unknown@leafai.dev")
    res = client.post(
        "/api/predict",
        headers=headers,
        data={"crop": "banana"},
        files={"file": ("a.jpg", _jpeg(), "image/jpeg")},
    )
    assert res.status_code == 422


def test_predict_crop_without_model_rejected(client):
    model_registry.unregister("mangosteen")
    headers = _auth_headers(client, "mc_nomodel@leafai.dev")
    res = client.post(
        "/api/predict",
        headers=headers,
        data={"crop": "mangosteen"},
        files={"file": ("a.jpg", _jpeg(), "image/jpeg")},
    )
    assert res.status_code == 422
    assert "Măng cụt" in res.json()["detail"]


def test_predict_durian_with_model_and_history_filter(client, fake_durian_model):
    headers = _auth_headers(client, "mc_durian@leafai.dev")
    res = client.post(
        "/api/predict",
        headers=headers,
        data={"crop": "durian"},
        files={"file": ("a.jpg", _jpeg(), "image/jpeg")},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["crop_code"] == "durian"
    assert body["status"] == "detected"
    assert body["detections"][0]["class_name"] == get_crop("durian").map_label("Leaf_Phytophthora")
    assert "sầu riêng" in body["summary"].lower()

    durian_hist = client.get("/api/history", headers=headers, params={"crop": "durian"}).json()
    tea_hist = client.get("/api/history", headers=headers, params={"crop": "tea"}).json()
    assert [h["id"] for h in durian_hist] == [body["id"]]
    assert durian_hist[0]["crop_code"] == "durian"
    assert tea_hist == []

    detail = client.get(f"/api/history/{body['id']}", headers=headers).json()
    assert detail["crop_code"] == "durian"
    assert detail["model_version"] == "durian-test"

    stats = client.get("/api/dashboard/stats", headers=headers).json()
    assert stats["crop_counts"] == {"durian": 1}
    assert stats["disease_distribution"] == {body["detections"][0]["class_name"]: 1}
    assert stats["recent_diagnoses"][0]["crop_code"] == "durian"


# ---------- /api/history/{id}/feedback ----------

def _create_diagnosis(client, headers) -> int:
    res = client.post("/api/predict", headers=headers, files={"file": ("a.jpg", _jpeg(), "image/jpeg")})
    assert res.status_code == 200, res.text
    return res.json()["id"]


def test_feedback_is_saved(client):
    headers = _auth_headers(client, "mc_feedback@leafai.dev")
    diag_id = _create_diagnosis(client, headers)

    res = client.post(f"/api/history/{diag_id}/feedback", headers=headers, json={"feedback": "incorrect"})
    assert res.status_code == 200
    assert res.json()["user_feedback"] == "incorrect"

    detail = client.get(f"/api/history/{diag_id}", headers=headers).json()
    assert detail["user_feedback"] == "incorrect"


def test_feedback_rejects_invalid_value(client):
    headers = _auth_headers(client, "mc_feedback_bad@leafai.dev")
    diag_id = _create_diagnosis(client, headers)
    res = client.post(f"/api/history/{diag_id}/feedback", headers=headers, json={"feedback": "maybe"})
    assert res.status_code == 422


def test_feedback_cannot_touch_other_users_records(client):
    owner = _auth_headers(client, "mc_owner@leafai.dev")
    intruder = _auth_headers(client, "mc_intruder@leafai.dev")
    diag_id = _create_diagnosis(client, owner)
    res = client.post(f"/api/history/{diag_id}/feedback", headers=intruder, json={"feedback": "correct"})
    assert res.status_code == 404


def test_feedback_requires_auth(client):
    assert client.post("/api/history/1/feedback", json={"feedback": "correct"}).status_code == 401


def test_predict_returns_503_when_default_crop_model_missing(client):
    from app.core.crops import get_crop

    headers = _auth_headers(client, "mc_tea_down@leafai.dev")
    original = model_registry.is_available
    model_registry.is_available = lambda crop: False if crop.code == "tea" else original(crop)
    try:
        res = client.post("/api/predict", headers=headers, files={"file": ("a.jpg", _jpeg(), "image/jpeg")})
    finally:
        model_registry.is_available = original
    assert res.status_code == 503
    assert get_crop("tea").name_vi  # sanity: crop still configured


class _ExplodingDetector(FakeDetector):
    def detect(self, image_path: str):
        raise RuntimeError("inference crashed")


def test_failed_inference_leaves_no_orphan_image(client):
    from app.core.config import settings

    headers = _auth_headers(client, "mc_orphan@leafai.dev")
    before = set(settings.originals_dir.iterdir())
    model_registry.register("durian", _ExplodingDetector())
    try:
        res = client.post("/api/predict", headers=headers, data={"crop": "durian"},
                          files={"file": ("a.jpg", _jpeg(), "image/jpeg")})
    finally:
        model_registry.unregister("durian")
    assert res.status_code == 500
    assert "inference crashed" not in res.text
    assert set(settings.originals_dir.iterdir()) == before

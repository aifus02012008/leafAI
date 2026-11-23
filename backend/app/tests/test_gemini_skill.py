"""Gemini leaf skill: schema validation, outcome mapping, and its use in /api/predict."""
import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.crops import get_crop
from app.db.init_db import init_database
from app.main import app
from app.services import gemini_skill
from app.services.detection_rules import RawDetection
from app.services.gemini_skill import GeminiLeafVerdict, parse_verdict, response_schema
from app.services.gemini_skill import service as skill_service
from app.services.model_registry import model_registry
from app.services.prediction_service import gemini_outcome
from app.tests.helpers import jpeg, register

NAMES = ["Thán thư măng cụt (Mangosteen anthracnose)", "Đốm rong măng cụt (Mangosteen algal leaf spot)"]


@pytest.fixture(scope="module", autouse=True)
def _db():
    init_database()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def gemini_on(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(settings, "GEMINI_VISION_ENABLED", True)
    gemini_skill.reset_cache()
    yield
    gemini_skill.reset_cache()


def _fake_gemini(monkeypatch, payload: dict, calls: list | None = None):
    def fake_call(image, prompt, schema):
        if calls is not None:
            calls.append({"prompt": prompt, "schema": schema, "bytes": len(image)})
        return payload

    monkeypatch.setattr(skill_service, "_call", fake_call)


# ---------- schema (pure) ----------

def test_schema_restricts_label_to_library():
    schema = response_schema(NAMES)
    assert schema["properties"]["label"]["enum"] == [*NAMES, "healthy", "unknown"]
    assert set(schema["required"]) == {"label", "confidence", "reason"}


def test_parse_disease_with_box():
    v = parse_verdict({"label": NAMES[0], "confidence": 0.82, "box": {"x1": 0.6, "y1": 0.1, "x2": 0.2, "y2": 0.5}, "reason": "Đốm nâu"}, NAMES)
    assert v.status == "diseased" and v.disease == NAMES[0]
    assert v.box == (0.2, 0.1, 0.6, 0.5)  # corners are re-ordered


@pytest.mark.parametrize(
    "payload",
    [
        {"label": "Bệnh lạ không có trong thư viện", "confidence": 0.99, "reason": ""},
        {"label": "unknown", "confidence": 0.9, "reason": "ảnh mờ"},
        "not a dict",
        {},
    ],
)
def test_parse_anything_else_is_unknown(payload):
    assert parse_verdict(payload, NAMES).status == "unknown"


def test_parse_clamps_confidence_and_drops_bad_box():
    v = parse_verdict({"label": NAMES[1], "confidence": 7, "box": {"x1": "a"}, "reason": "x" * 999}, NAMES)
    assert v.confidence == 1.0 and v.box is None and len(v.reason) == 300


# ---------- outcome mapping ----------

def test_gemini_outcome_maps_box_to_pixels():
    out = gemini_outcome(GeminiLeafVerdict("diseased", NAMES[0], 0.8, (0.25, 0.5, 0.75, 1.0), "r"), (200, 100))
    assert out.status == "detected" and out.source == "gemini"
    assert out.detections[0]["x1"] == 50 and out.detections[0]["y2"] == 100


def test_gemini_outcome_rejects_low_confidence_and_unknown():
    assert gemini_outcome(GeminiLeafVerdict("diseased", NAMES[0], 0.3, None, ""), (10, 10)) is None
    assert gemini_outcome(GeminiLeafVerdict("unknown", None, 0.9, None, ""), (10, 10)) is None


def test_disabled_without_key(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    assert not gemini_skill.is_enabled()


def test_cache_and_rate_limit(gemini_on, monkeypatch, tmp_path):
    calls: list = []
    _fake_gemini(monkeypatch, {"label": NAMES[0], "confidence": 0.9, "reason": "r"}, calls)
    img = tmp_path / "a.jpg"
    img.write_bytes(jpeg().getvalue())
    crop = get_crop("mangosteen")
    diseases = [{"class_name": n, "symptoms": ""} for n in NAMES]
    first = gemini_skill.diagnose_leaf(str(img), crop, diseases, user_id=1)
    second = gemini_skill.diagnose_leaf(str(img), crop, diseases, user_id=1)
    assert first == second and len(calls) == 1  # identical photo served from cache
    assert NAMES[0] in calls[0]["prompt"]


# ---------- /api/predict integration ----------

def test_crops_report_gemini_mode(client, gemini_on):
    model_registry.unregister("mangosteen")
    crops = {c["code"]: c for c in client.get("/api/crops").json()}
    assert crops["mangosteen"]["is_available"] is True
    assert crops["mangosteen"]["diagnosis_mode"] == "gemini"
    assert crops["tea"]["diagnosis_mode"] == "model"


def test_predict_mangosteen_via_gemini(client, gemini_on, monkeypatch):
    model_registry.unregister("mangosteen")
    _fake_gemini(monkeypatch, {
        "label": "Thán thư măng cụt (Mangosteen anthracnose)", "confidence": 0.86,
        "box": {"x1": 0.1, "y1": 0.1, "x2": 0.6, "y2": 0.6}, "reason": "Đốm nâu viền vàng.",
    })
    headers = register(client, "gemini_mc@leafai.dev")
    res = client.post(
        "/api/predict", headers=headers,
        data={"crop": "mangosteen", "share_to_radar": "true", "latitude": "10.2", "longitude": "106.3"},
        files={"file": ("a.jpg", jpeg(), "image/jpeg")},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["analysis_source"] == "gemini"
    assert body["detections"][0]["class_name"].startswith("Thán thư măng cụt")
    assert body["summary"].startswith("AI tham khảo (Gemini)")
    # treatment plan + actives are reachable for the Gemini diagnosis
    diseases = client.get("/api/diseases", params={"crop": "mangosteen"}).json()
    assert any(d["class_name"] == body["detections"][0]["class_name"] for d in diseases)


def test_predict_gemini_unclear_asks_for_retake(client, gemini_on, monkeypatch):
    model_registry.unregister("rambutan")
    _fake_gemini(monkeypatch, {"label": "unknown", "confidence": 0.2, "reason": "Ảnh mờ."})
    headers = register(client, "gemini_unclear@leafai.dev")
    res = client.post("/api/predict", headers=headers, data={"crop": "rambutan"}, files={"file": ("a.jpg", jpeg(), "image/jpeg")})
    assert res.status_code == 422
    assert "chụp" in res.json()["detail"]


def test_predict_gemini_outage_returns_503(client, gemini_on, monkeypatch):
    model_registry.unregister("rambutan")

    def boom(*a, **k):
        raise gemini_skill.GeminiSkillError("down")

    monkeypatch.setattr(skill_service, "_call", boom)
    headers = register(client, "gemini_down@leafai.dev")
    res = client.post("/api/predict", headers=headers, data={"crop": "rambutan"}, files={"file": ("a.jpg", jpeg(), "image/jpeg")})
    assert res.status_code == 503


class _BlindModel:
    """A crop model that sees nothing (inconclusive)."""

    version = "blind"
    class_names = {0: "Healthy"}
    kind = "detect"

    def detect(self, image_path: str) -> list[RawDetection]:
        return []


def test_model_inconclusive_falls_back_to_gemini(client, gemini_on, monkeypatch):
    model_registry.register("durian", _BlindModel())
    try:
        _fake_gemini(monkeypatch, {"label": "healthy", "confidence": 0.9, "reason": "Lá xanh đều."})
        headers = register(client, "gemini_fallback@leafai.dev")
        res = client.post("/api/predict", headers=headers, data={"crop": "durian"}, files={"file": ("a.jpg", jpeg(), "image/jpeg")})
        assert res.status_code == 200, res.text
        body = res.json()
        assert body["analysis_source"] == "gemini" and body["status"] == "no_detection"
    finally:
        model_registry.unregister("durian")


def test_model_inconclusive_without_gemini_keeps_model_result(client, monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    model_registry.register("durian", _BlindModel())
    try:
        headers = register(client, "gemini_off@leafai.dev")
        res = client.post("/api/predict", headers=headers, data={"crop": "durian"}, files={"file": ("a.jpg", jpeg(), "image/jpeg")})
        assert res.status_code == 200 and res.json()["analysis_source"] == "model"
    finally:
        model_registry.unregister("durian")


def test_schema_is_json_serialisable():
    json.dumps(response_schema(NAMES), ensure_ascii=False)


class _Resp:
    def __init__(self, payload, status=200):
        self._payload, self.status_code = payload, status

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            raise httpx.HTTPStatusError("boom", request=None, response=self)

    def json(self):
        return self._payload


def test_call_sends_image_schema_and_header_key(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "g-key")
    sent = {}

    def fake_post(url, headers, json, timeout):
        sent.update(url=url, headers=headers, body=json, timeout=timeout)
        text = '{"label": "healthy", "confidence": 0.9, "reason": "ok"}'
        return _Resp({"candidates": [{"content": {"parts": [{"text": "suy nghĩ", "thought": True}, {"text": text}]}}]})

    monkeypatch.setattr(skill_service.httpx, "post", fake_post)
    out = skill_service._call(b"jpegbytes", "prompt", response_schema(NAMES))
    assert out["label"] == "healthy"
    assert "key=" not in sent["url"] and sent["headers"]["x-goog-api-key"] == "g-key"
    parts = sent["body"]["contents"][0]["parts"]
    assert parts[0]["inlineData"]["mimeType"] == "image/jpeg"
    assert sent["body"]["generationConfig"]["responseMimeType"] == "application/json"
    assert sent["timeout"] == settings.GEMINI_VISION_TIMEOUT_SECONDS


@pytest.mark.parametrize("response", [_Resp({}, status=503), _Resp({"candidates": []}), _Resp({"candidates": [{"content": {"parts": [{"text": "not json"}]}}]})])
def test_call_errors_become_skill_error(monkeypatch, response):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "g-key")
    monkeypatch.setattr(skill_service.httpx, "post", lambda *a, **k: response)
    with pytest.raises(gemini_skill.GeminiSkillError):
        skill_service._call(b"x", "p", {})


def test_rate_limit_per_user(gemini_on, monkeypatch, tmp_path):
    from app.core.rate_limit import reset_rate_limits

    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "GEMINI_VISION_PER_MINUTE", 1)
    reset_rate_limits()
    _fake_gemini(monkeypatch, {"label": "healthy", "confidence": 0.9, "reason": ""})
    crop = get_crop("rambutan")
    for i, colour in enumerate([(10, 120, 10), (200, 30, 30)]):
        img = tmp_path / f"{i}.jpg"
        from PIL import Image
        Image.new("RGB", (32, 32), colour).save(img)
        if i == 0:
            gemini_skill.diagnose_leaf(str(img), crop, [], user_id=7)
        else:
            with pytest.raises(gemini_skill.GeminiSkillRateLimited):
                gemini_skill.diagnose_leaf(str(img), crop, [], user_id=7)

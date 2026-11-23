"""Tests for the Vietnamese Q&A assistant (retrieval + optional LLM)."""
import pytest
from fastapi.testclient import TestClient

from app.db.init_db import init_database
from app.db.session import SessionLocal
from app.main import app
from app.models.user import User
from app.services import assistant_service
from app.services.assistant_service import retrieve_context


@pytest.fixture(scope="module", autouse=True)
def _db():
    init_database()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def headers(client):
    email = "assistant_user@leafai.dev"
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
    assistant_service.reset_rate_limits()
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_retrieval_finds_relevant_disease():
    db = SessionLocal()
    try:
        hits = retrieve_context(db, "lá sầu riêng bị cháy do phytophthora phải làm sao", crop_code=None)
    finally:
        db.close()
    assert hits
    assert "Phytophthora" in hits[0].class_name


def test_retrieval_respects_crop_filter():
    db = SessionLocal()
    try:
        hits = retrieve_context(db, "bệnh thán thư", crop_code="rambutan")
    finally:
        db.close()
    assert hits and all(h.crop_code == "rambutan" for h in hits)


def test_ask_without_llm_key_uses_library_answer(client, headers, monkeypatch):
    monkeypatch.setattr(assistant_service, "_llm_answer", lambda *a, **k: None)
    res = client.post("/api/assistant/ask", headers=headers, json={"question": "lá chôm chôm có lớp phấn trắng"})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["source"] == "library"
    assert "Phấn trắng" in body["answer"]
    assert body["related"][0]["crop_code"] == "rambutan"


def test_ask_uses_llm_when_available(client, headers, monkeypatch):
    captured = {}

    def fake_llm(question, contexts):
        captured["question"] = question
        captured["contexts"] = contexts
        return "Câu trả lời từ AI."

    monkeypatch.setattr(assistant_service, "_llm_answer", fake_llm)
    res = client.post("/api/assistant/ask", headers=headers, json={"question": "sầu riêng bị thán thư", "crop": "durian"})
    body = res.json()
    assert body["source"] == "ai"
    assert body["answer"].startswith("Câu trả lời từ AI.")
    assert captured["contexts"]


def test_ask_validation(client, headers):
    assert client.post("/api/assistant/ask", headers=headers, json={"question": ""}).status_code == 422
    assert client.post("/api/assistant/ask", headers=headers, json={"question": "x" * 600}).status_code == 422


def test_ask_requires_auth(client):
    assert client.post("/api/assistant/ask", json={"question": "hello"}).status_code == 401


def test_ask_rate_limited(client, headers, monkeypatch):
    monkeypatch.setattr(assistant_service, "_llm_answer", lambda *a, **k: None)
    monkeypatch.setattr(assistant_service, "RATE_LIMIT_PER_MINUTE", 2)
    codes = [client.post("/api/assistant/ask", headers=headers, json={"question": "thán thư"}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


class _FakeResponse:
    def __init__(self, payload, status=200):
        self._payload, self.status_code = payload, status

    def raise_for_status(self):
        if self.status_code >= 400:
            import httpx
            raise httpx.HTTPStatusError("boom", request=None, response=None)

    def json(self):
        return self._payload


def test_llm_answer_calls_messages_api(monkeypatch):
    from app.core.config import settings

    calls = {}

    def fake_post(url, headers, json, timeout):
        calls.update(url=url, headers=headers, body=json)
        return _FakeResponse({"content": [{"type": "text", "text": "Trả lời ngắn."}]})

    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(settings, "ASSISTANT_PROVIDER", "anthropic")
    monkeypatch.setattr(assistant_service.httpx, "post", fake_post)
    out = assistant_service._llm_answer("hỏi gì đó", [])
    assert out == "Trả lời ngắn."
    assert calls["url"].endswith("/v1/messages")
    assert calls["headers"]["x-api-key"] == "test-key"
    assert calls["body"]["model"] == settings.ASSISTANT_MODEL
    assert "liều" in calls["body"]["system"]


def test_llm_answer_falls_back_on_error(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setattr(assistant_service.httpx, "post", lambda *a, **k: _FakeResponse({}, status=500))
    assert assistant_service._llm_answer("q", []) is None


def test_llm_disabled_without_key(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", None)
    assert assistant_service._llm_answer("q", []) is None


# ---------- Gemini (default provider) ----------

def test_provider_auto_prefers_gemini(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "ASSISTANT_PROVIDER", "auto")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "g-key")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "a-key")
    assert assistant_service.active_provider() == "gemini"
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    assert assistant_service.active_provider() == "anthropic"
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", None)
    assert assistant_service.active_provider() is None


def test_gemini_call_uses_header_key_and_system_prompt(monkeypatch):
    from app.core.config import settings

    calls = {}

    def fake_post(url, headers, json, timeout):
        calls.update(url=url, headers=headers, body=json)
        return _FakeResponse({"candidates": [{"content": {"parts": [{"text": "Trả lời "}, {"text": "từ Gemini."}]}}]})

    monkeypatch.setattr(settings, "ASSISTANT_PROVIDER", "auto")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "g-key")
    monkeypatch.setattr(settings, "GEMINI_MODEL", "gemini-test")
    monkeypatch.setattr(assistant_service.httpx, "post", fake_post)
    assert assistant_service._llm_answer("hỏi", []) == "Trả lời từ Gemini."
    assert calls["url"].endswith("/models/gemini-test:generateContent")
    assert "key=" not in calls["url"]  # key travels in a header, never in the URL (keeps it out of logs)
    assert calls["headers"]["x-goog-api-key"] == "g-key"
    assert "liều" in calls["body"]["systemInstruction"]["parts"][0]["text"]


def test_gemini_blocked_or_empty_response_falls_back(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "GEMINI_API_KEY", "g-key")
    monkeypatch.setattr(assistant_service.httpx, "post", lambda *a, **k: _FakeResponse({"promptFeedback": {"blockReason": "SAFETY"}}))
    assert assistant_service._llm_answer("q", []) is None
    monkeypatch.setattr(assistant_service.httpx, "post", lambda *a, **k: _FakeResponse({}, status=429))
    assert assistant_service._llm_answer("q", []) is None

"""Production hardening: secret validation, password check, rate limits, security headers."""
import pytest
from fastapi.testclient import TestClient

from app.core.config import DEV_SECRET_KEY, Settings, settings, validate_production_settings
from app.core.security import hash_password, verify_password
from app.db.init_db import init_database
from app.main import app


@pytest.fixture(scope="module", autouse=True)
def _db():
    init_database()


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ---------- production settings ----------

def test_production_rejects_default_secret():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_production_settings(Settings(APP_ENV="production", SECRET_KEY=DEV_SECRET_KEY, CRON_SECRET="x" * 32))


def test_production_rejects_short_secret():
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        validate_production_settings(Settings(APP_ENV="production", SECRET_KEY="short", CRON_SECRET="x" * 32))


def test_production_accepts_strong_secret():
    validate_production_settings(Settings(APP_ENV="production", SECRET_KEY="k" * 48, CRON_SECRET="c" * 32))


def test_development_allows_default_secret():
    validate_production_settings(Settings(APP_ENV="development", SECRET_KEY=DEV_SECRET_KEY))


# ---------- passwords ----------

def test_password_aliases_are_not_accepted():
    hashed = hash_password("03112007")
    assert verify_password("03112007", hashed)
    assert not verify_password("031107", hashed)


# ---------- headers ----------

def test_security_headers_present(client):
    res = client.get("/api/health")
    assert res.headers["X-Content-Type-Options"] == "nosniff"
    assert res.headers["X-Frame-Options"] == "DENY"
    assert res.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "geolocation=(self)" in res.headers["Permissions-Policy"]
    assert "microphone=(self)" in res.headers["Permissions-Policy"]


# ---------- rate limits ----------

def test_login_is_rate_limited(client, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "AUTH_RATE_LIMIT_PER_MINUTE", 3)
    body = {"email": "nobody@leafai.dev", "password": "WrongPassword1!"}
    codes = [client.post("/api/auth/login", json=body).status_code for _ in range(4)]
    assert codes[:3] == [401, 401, 401]
    assert codes[3] == 429


def test_predict_is_rate_limited_per_user(client, monkeypatch):
    from io import BytesIO
    from PIL import Image

    pw = "Password123!"
    email = "ratelimit_predict@leafai.dev"
    from app.db.session import SessionLocal
    from app.models.user import User
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == email).first()
        if u:
            db.delete(u)
            db.commit()
    finally:
        db.close()
    token = client.post("/api/auth/register", json={"email": email, "password": pw, "password_confirmation": pw}).json()["access_token"]
    monkeypatch.setattr(settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(settings, "PREDICT_RATE_LIMIT_PER_MINUTE", 1)

    def send():
        buf = BytesIO()
        Image.new("RGB", (64, 64), (40, 150, 40)).save(buf, format="JPEG")
        buf.seek(0)
        return client.post("/api/predict", headers={"Authorization": f"Bearer {token}"},
                           files={"file": ("a.jpg", buf, "image/jpeg")}).status_code

    assert send() == 200
    assert send() == 429


def test_oversized_credentials_rejected(client):
    long_pw = "x" * 129
    assert client.post("/api/auth/login", json={"email": "a@b.dev", "password": long_pw}).status_code == 422
    assert client.post("/api/auth/register", json={"email": "a@b.dev", "password": long_pw,
                                                    "password_confirmation": long_pw}).status_code == 422
    assert client.post("/api/auth/login", json={"email": "a" * 250 + "@b.dev", "password": "x"}).status_code == 422

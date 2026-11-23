"""Small helpers shared by API tests."""
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.db.session import SessionLocal
from app.models.user import User

PASSWORD = "Password123!"


def register(client: TestClient, email: str) -> dict[str, str]:
    """(Re)create a user and return auth headers."""
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            db.delete(existing)
            db.commit()
    finally:
        db.close()
    res = client.post("/api/auth/register", json={"email": email, "password": PASSWORD, "password_confirmation": PASSWORD})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def jpeg() -> BytesIO:
    buf = BytesIO()
    Image.new("RGB", (64, 64), (60, 140, 60)).save(buf, format="JPEG")
    buf.seek(0)
    return buf


def user_id(email: str) -> int:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.email == email).one().id
    finally:
        db.close()

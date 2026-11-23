import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from PIL import Image
from app.main import app
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.db.init_db import init_database
from app.models.user import User
from app.models.diagnosis import DiagnosisHistory

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    init_database()
    yield

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True
    assert len(data["model_classes"]) == 6

def test_diseases_catalog(client):
    res = client.get("/api/diseases", params={"crop": "tea"})
    assert res.status_code == 200
    diseases = res.json()
    assert len(diseases) == 6
    
    # Detail check
    first_id = diseases[0]["id"]
    res_detail = client.get(f"/api/diseases/{first_id}")
    assert res_detail.status_code == 200
    assert "symptoms" in res_detail.json()
    assert "prevention" in res_detail.json()

def test_auth_workflow(client):
    email = "testuser@leafai.dev"
    password = "SecurePassword123"
    
    # Clean up existing if rerun
    db = SessionLocal()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        db.delete(existing)
        db.commit()
    db.close()
    
    # 1. Register
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "password_confirmation": password
    })
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == email
    token = reg_data["access_token"]
    
    # 2. Duplicate registration rejection
    dup_res = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "password_confirmation": password
    })
    assert dup_res.status_code == 409
    
    # 3. Login with wrong password
    bad_login = client.post("/api/auth/login", json={
        "email": email,
        "password": "WrongPassword!"
    })
    assert bad_login.status_code == 401
    
    # 4. Login with correct credentials
    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()
    
    # 5. Access /api/auth/me
    headers = {"Authorization": f"Bearer {token}"}
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == email
    
    # 6. Access without token should be 401
    unauth_res = client.get("/api/auth/me")
    assert unauth_res.status_code == 401

def test_dashboard_and_history_isolation(client):
    # Register User A
    user_a_email = "user_a@leafai.dev"
    pw = "Password123!"
    
    db = SessionLocal()
    for em in [user_a_email, "user_b@leafai.dev"]:
        u = db.query(User).filter(User.email == em).first()
        if u:
            db.delete(u)
    db.commit()
    db.close()
    
    res_a = client.post("/api/auth/register", json={
        "email": user_a_email,
        "password": pw,
        "password_confirmation": pw
    })
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    
    # Register User B
    res_b = client.post("/api/auth/register", json={
        "email": "user_b@leafai.dev",
        "password": pw,
        "password_confirmation": pw
    })
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    
    # Check stats for A
    stats_a = client.get("/api/dashboard/stats", headers=headers_a)
    assert stats_a.status_code == 200
    assert stats_a.json()["total_diagnoses"] == 0

def test_predict_validation_and_inference(client):
    # Register test user
    email = "predict_user@leafai.dev"
    pw = "Password123!"
    db = SessionLocal()
    u = db.query(User).filter(User.email == email).first()
    if u:
        db.delete(u)
        db.commit()
    db.close()
    
    res = client.post("/api/auth/register", json={
        "email": email,
        "password": pw,
        "password_confirmation": pw
    })
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Unauthenticated prediction must be rejected with 401
    unauth_pred = client.post("/api/predict")
    assert unauth_pred.status_code == 401
    
    # 2. Corrupt/Invalid image file rejection
    bad_file = {"file": ("bad.jpg", BytesIO(b"not-an-image-content"), "image/jpeg")}
    bad_res = client.post("/api/predict", headers=headers, files=bad_file)
    assert bad_res.status_code == 400
    
    # 3. Create valid image in memory
    img = Image.new("RGB", (640, 640), color=(40, 160, 40))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    
    # 4. Successful prediction request
    files = {"file": ("test_leaf.jpg", buf, "image/jpeg")}
    pred_res = client.post("/api/predict", headers=headers, files=files)
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert "status" in pred_data
    assert pred_data["status"] in ("detected", "no_detection")
    assert "original_image_url" in pred_data
    
    history_id = pred_data["id"]
    
    # 5. Verify it appears in user's history
    hist_res = client.get("/api/history", headers=headers)
    assert hist_res.status_code == 200
    hist_items = hist_res.json()
    assert len(hist_items) >= 1
    assert any(h["id"] == history_id for h in hist_items)
    
    # 6. Verify image access via /api/images/originals/...
    orig_url = pred_data["original_image_url"]
    img_res = client.get(orig_url)
    assert img_res.status_code == 200
    assert img_res.headers["content-type"].startswith("image/")
    
    # 7. Test delete record
    del_res = client.delete(f"/api/history/{history_id}", headers=headers)
    assert del_res.status_code == 200
    
    # 8. Verify record is now 404
    get_after_del = client.get(f"/api/history/{history_id}", headers=headers)
    assert get_after_del.status_code == 404

def test_predict_healthy_leaf(client):
    email = "healthy_test@leafai.dev"
    pw = "Password123!"
    db = SessionLocal()
    u = db.query(User).filter(User.email == email).first()
    if u:
        db.delete(u)
        db.commit()
    db.close()
    
    res = client.post("/api/auth/register", json={
        "email": email,
        "password": pw,
        "password_confirmation": pw
    })
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    from pathlib import Path
    sample_healthy = Path("backend/app/storage/originals/334e1f8bccb3_orig.jpg")
    if not sample_healthy.exists():
        sample_healthy = Path("app/storage/originals/334e1f8bccb3_orig.jpg")
    if sample_healthy.exists():
        with open(sample_healthy, "rb") as f:
            file_bytes = f.read()
    else:
        img = Image.new("RGB", (640, 640), color=(34, 139, 34))
        buf = BytesIO()
        img.save(buf, format="JPEG")
        file_bytes = buf.getvalue()
        
    files = {"file": ("healthy_leaf.jpg", BytesIO(file_bytes), "image/jpeg")}
    pred_res = client.post("/api/predict", headers=headers, files=files)
    assert pred_res.status_code == 200
    pred_data = pred_res.json()
    assert pred_data["status"] == "no_detection"
    assert len(pred_data["detections"]) == 0
    assert "khỏe mạnh" in pred_data["summary"].lower()

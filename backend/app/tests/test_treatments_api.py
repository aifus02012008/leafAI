"""Integration tests: actives catalog, calculators, treatment log, follow-up verdicts, efficacy stats."""
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


@pytest.fixture(scope="module", autouse=True)
def _db():
    init_database()
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


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


def _diagnose(client, headers) -> int:
    buf = BytesIO()
    Image.new("RGB", (320, 320), (60, 140, 60)).save(buf, format="JPEG")
    buf.seek(0)
    res = client.post("/api/predict", headers=headers, files={"file": ("a.jpg", buf, "image/jpeg")})
    assert res.status_code == 200, res.text
    return res.json()["id"]


def _set_severity(diag_id: int, pct: float) -> None:
    db = SessionLocal()
    try:
        db.get(DiagnosisHistory, diag_id).severity_pct = pct
        db.commit()
    finally:
        db.close()


# ---------- catalog & calculators ----------

def test_actives_recommended_for_disease_first(client):
    disease = "Cháy nâu lá chè (Brown blight of tea)"
    res = client.get("/api/actives", params={"crop": "tea", "disease": disease})
    assert res.status_code == 200
    items = res.json()
    assert items[0]["recommended"] is True
    assert all(not a["banned"] or not a["recommended"] for a in items)
    assert any(a["code"] == "carbendazim" and a["banned"] for a in items)


def test_dose_endpoint(client):
    res = client.post("/api/tools/dose", json={
        "area": 1, "area_unit": "ha", "tank_l": 16, "label_dose": 20,
        "label_dose_basis": "per_tank", "label_tank_l": 16, "water_l_per_ha": 500,
        "pack_size": 100, "pack_price": 45000,
    })
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["tanks_needed"] == 32
    assert body["total_product"] == 625
    assert body["estimated_cost"] == 7 * 45000


def test_dose_endpoint_validation_error(client):
    res = client.post("/api/tools/dose", json={
        "area": 1, "area_unit": "acre", "tank_l": 16, "label_dose": 20,
        "label_dose_basis": "per_tank", "label_tank_l": 16, "water_l_per_ha": 500,
    })
    assert res.status_code == 422


def test_harvest_date_endpoint(client):
    today = date.today()
    res = client.post("/api/tools/harvest-date", json={"sprays": [
        {"applied_on": today.isoformat(), "phi_days": 7},
        {"applied_on": (today - timedelta(days=2)).isoformat(), "phi_days": 14},
    ]})
    assert res.status_code == 200
    body = res.json()
    assert body["harvest_safe_on"] == (today + timedelta(days=12)).isoformat()
    assert body["days_remaining"] == 12


# ---------- treatment lifecycle ----------

def test_treatment_lifecycle_effective(client):
    headers = _auth(client, "tr_effective@leafai.dev")
    diag = _diagnose(client, headers)
    _set_severity(diag, 12.0)

    res = client.post("/api/treatments", headers=headers, json={
        "diagnosis_id": diag, "active_code": "azoxystrobin", "product_name": "Thuốc A",
        "phi_days": 7, "followup_days": 4, "area_m2": 500,
    })
    assert res.status_code == 201, res.text
    tr = res.json()
    assert tr["severity_before"] == 12.0
    assert tr["status"] == "awaiting_followup"
    assert tr["followup_due_on"] == (date.today() + timedelta(days=4)).isoformat()
    assert tr["harvest_safe_on"] == (date.today() + timedelta(days=7)).isoformat()
    assert tr["crop_code"] == "tea"

    listed = client.get("/api/treatments", headers=headers).json()
    assert [t["id"] for t in listed] == [tr["id"]]

    follow_diag = _diagnose(client, headers)
    _set_severity(follow_diag, 12.5)
    res = client.post(f"/api/treatments/{tr['id']}/followups", headers=headers, json={"diagnosis_id": follow_diag})
    assert res.status_code == 201, res.text
    body = res.json()
    assert body["verdict"] == "effective"
    assert body["rotation_suggestions"] == []

    detail = client.get(f"/api/treatments/{tr['id']}", headers=headers).json()
    assert detail["status"] == "evaluated"
    assert detail["followups"][0]["verdict"] == "effective"


def test_ineffective_followup_suggests_other_moa_group(client):
    headers = _auth(client, "tr_ineffective@leafai.dev")
    diag = _diagnose(client, headers)
    _set_severity(diag, 10.0)
    tr = client.post("/api/treatments", headers=headers, json={
        "diagnosis_id": diag, "active_code": "difenoconazole",
        "disease_name": "Cháy nâu lá chè (Brown blight of tea)",
    }).json()

    follow = _diagnose(client, headers)
    _set_severity(follow, 18.0)
    body = client.post(f"/api/treatments/{tr['id']}/followups", headers=headers, json={"diagnosis_id": follow}).json()
    assert body["verdict"] == "ineffective"
    assert body["checklist"]
    codes = [s["code"] for s in body["rotation_suggestions"]]
    assert codes and "hexaconazole" not in codes and "difenoconazole" not in codes


def test_banned_active_rejected(client):
    headers = _auth(client, "tr_banned@leafai.dev")
    diag = _diagnose(client, headers)
    res = client.post("/api/treatments", headers=headers, json={"diagnosis_id": diag, "active_code": "carbendazim"})
    assert res.status_code == 422
    assert "cấm" in res.json()["detail"]


def test_unknown_active_rejected(client):
    headers = _auth(client, "tr_unknown@leafai.dev")
    diag = _diagnose(client, headers)
    res = client.post("/api/treatments", headers=headers, json={"diagnosis_id": diag, "active_code": "nope"})
    assert res.status_code == 422


def test_cannot_use_other_users_diagnosis(client):
    owner = _auth(client, "tr_owner@leafai.dev")
    intruder = _auth(client, "tr_intruder@leafai.dev")
    diag = _diagnose(client, owner)
    res = client.post("/api/treatments", headers=intruder, json={"diagnosis_id": diag, "active_code": "mancozeb"})
    assert res.status_code == 404


def test_cannot_read_or_followup_other_users_treatment(client):
    owner = _auth(client, "tr_owner2@leafai.dev")
    intruder = _auth(client, "tr_intruder2@leafai.dev")
    tr = client.post("/api/treatments", headers=owner, json={
        "diagnosis_id": _diagnose(client, owner), "active_code": "mancozeb"}).json()
    assert client.get(f"/api/treatments/{tr['id']}", headers=intruder).status_code == 404
    res = client.post(f"/api/treatments/{tr['id']}/followups", headers=intruder,
                      json={"diagnosis_id": _diagnose(client, intruder)})
    assert res.status_code == 404
    assert client.delete(f"/api/treatments/{tr['id']}", headers=intruder).status_code == 404
    assert client.delete(f"/api/treatments/{tr['id']}", headers=owner).status_code == 200


def test_followup_requires_new_diagnosis(client):
    headers = _auth(client, "tr_samediag@leafai.dev")
    diag = _diagnose(client, headers)
    tr = client.post("/api/treatments", headers=headers, json={"diagnosis_id": diag, "active_code": "mancozeb"}).json()
    res = client.post(f"/api/treatments/{tr['id']}/followups", headers=headers, json={"diagnosis_id": diag})
    assert res.status_code == 422


def test_treatment_requires_auth(client):
    assert client.get("/api/treatments").status_code == 401


def test_efficacy_stats_respect_minimum_sample(client):
    headers = _auth(client, "tr_stats@leafai.dev")
    res = client.get("/api/treatments/stats/efficacy", headers=headers, params={"min_samples": 5})
    assert res.status_code == 200
    rows = res.json()
    assert all(r["samples"] >= 5 for r in rows)
    assert all(0 <= r["effective_rate"] <= 1 for r in rows)
    res = client.get("/api/treatments/stats/efficacy", headers=headers, params={"min_samples": 0})
    assert res.status_code == 422


def test_efficacy_minimum_sample_is_enforced_server_side(client):
    headers = _auth(client, "tr_stats_min@leafai.dev")
    assert client.get("/api/treatments/stats/efficacy", headers=headers, params={"min_samples": 4}).status_code == 422


def test_free_text_disease_name_is_replaced_by_library_name(client):
    headers = _auth(client, "tr_freetext@leafai.dev")
    diag = _diagnose(client, headers)
    tr = client.post("/api/treatments", headers=headers, json={
        "diagnosis_id": diag, "active_code": "mancozeb", "disease_name": "<script>spam</script>",
    }).json()
    assert tr["disease_name"] != "<script>spam</script>"


def test_followup_photo_must_be_newer_and_not_reused(client):
    headers = _auth(client, "tr_order@leafai.dev")
    old_diag = _diagnose(client, headers)
    diag = _diagnose(client, headers)
    tr = client.post("/api/treatments", headers=headers, json={"diagnosis_id": diag, "active_code": "mancozeb"}).json()
    res = client.post(f"/api/treatments/{tr['id']}/followups", headers=headers, json={"diagnosis_id": old_diag})
    assert res.status_code == 422

    new_diag = _diagnose(client, headers)
    ok = client.post(f"/api/treatments/{tr['id']}/followups", headers=headers, json={"diagnosis_id": new_diag})
    assert ok.status_code == 201
    dup = client.post(f"/api/treatments/{tr['id']}/followups", headers=headers, json={"diagnosis_id": new_diag})
    assert dup.status_code == 422


def test_out_of_range_dates_rejected(client):
    res = client.post("/api/tools/harvest-date", json={"sprays": [{"applied_on": "9999-12-31", "phi_days": 7}]})
    assert res.status_code == 422

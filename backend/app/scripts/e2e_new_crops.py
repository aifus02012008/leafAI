"""End-to-end check of the new-crop flow (durian model, mangosteen/rambutan via the Gemini leaf skill).

For each crop: upload a leaf photo -> disease + box -> treatment plan & actives -> "Hỏi bác sĩ AI" chat
with diagnosis context -> radar alert with the per-disease weather profile.

Runs in-process against a throw-away SQLite database. Gemini is stubbed by default so the script is
deterministic and free; pass --live-gemini to call the real API (needs GEMINI_API_KEY).

    cd backend
    .venv/Scripts/python.exe -m app.scripts.e2e_new_crops --durian-image ../datasets/durian/cls/test/Leaf_Algal/<file>.jpg
"""
from __future__ import annotations

import argparse
import os
import secrets
import sys
import tempfile
from pathlib import Path

# Isolated database + storage, set before the app is imported.
_TMP = Path(tempfile.mkdtemp(prefix="leafai_e2e_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'e2e.db').as_posix()}"
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

from datetime import date, timedelta  # noqa: E402

from fastapi.testclient import TestClient  # noqa: E402
from PIL import Image  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.main import app  # noqa: E402
from app.services import gemini_skill, weather_service  # noqa: E402
from app.services.gemini_skill import service as skill_service  # noqa: E402
from app.services.radar_rules import DayWeather  # noqa: E402

STUB_ANSWERS = {
    "mangosteen": {"label": "Thán thư măng cụt (Mangosteen anthracnose)", "confidence": 0.84,
                   "box": {"x1": 0.2, "y1": 0.2, "x2": 0.7, "y2": 0.7}, "reason": "Đốm nâu viền vàng ở mép lá."},
    "rambutan": {"label": "Phấn trắng chôm chôm (Rambutan powdery mildew)", "confidence": 0.79,
                 "box": None, "reason": "Lớp bột trắng trên lá non."},
}
WET_WEEK = [DayWeather(day=date.today() + timedelta(days=i), humid_hours=10, rh_max=97, t_min=24, t_max=30, precip_mm=15) for i in range(3)]


def _placeholder_leaf(path: Path) -> Path:
    Image.new("RGB", (320, 240), (70, 140, 60)).save(path, "JPEG")
    return path


def _check(ok: bool, label: str) -> bool:
    print(f"  [{'OK ' if ok else 'FAIL'}] {label}")
    return ok


def run_crop(client: TestClient, headers: dict, crop: str, image: Path) -> bool:
    print(f"\n== {crop} ({image.name})")
    with image.open("rb") as fh:
        res = client.post(
            "/api/predict", headers=headers,
            data={"crop": crop, "share_to_radar": "true", "latitude": "10.24", "longitude": "106.37"},
            files={"file": (image.name, fh, "image/jpeg")},
        )
    if not _check(res.status_code == 200, f"predict HTTP {res.status_code} {res.text[:120] if res.status_code != 200 else ''}"):
        return False
    body = res.json()
    det = body["detections"][0] if body["detections"] else None
    ok = _check(True, f"source={body['analysis_source']} status={body['status']} "
                      f"disease={det['class_name'] if det else '-'} conf={det['confidence'] if det else '-'}")
    ok &= _check(det is None or (det["x2"] > det["x1"] and det["y2"] > det["y1"]), "bounding box is valid")
    if det:
        diseases = client.get("/api/diseases", params={"crop": crop}).json()
        match = next((d for d in diseases if d["class_name"] == det["class_name"]), None)
        ok &= _check(match is not None, "disease is in the library")
        if match:
            detail = client.get(f"/api/diseases/{match['id']}").json()
            ok &= _check("Giai đoạn 1" in (detail.get("treatment_steps") or ""), "treatment plan has staged steps")
            actives = client.get("/api/actives", params={"crop": crop, "disease": det["class_name"]}, headers=headers).json()
            recommended = [x["name"] for x in actives if x.get("recommended")]
            ok &= _check(len(recommended) > 0, f"recommended actives: {', '.join(recommended[:4])}")
    chat = client.post("/api/assistant/ask", headers=headers, json={"question": "Xử lý thế nào?", "diagnosis_id": body["id"]})
    ok &= _check(chat.status_code == 200, f"chat with diagnosis context ({chat.json().get('source') if chat.status_code == 200 else chat.status_code})")
    if det and chat.status_code == 200:
        related = chat.json()["related"]
        ok &= _check(bool(related) and related[0]["class_name"] == det["class_name"], "chat grounded on the diagnosed disease")
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--durian-image", type=Path, help="real durian leaf photo (defaults to a plain green image)")
    parser.add_argument("--mangosteen-image", type=Path)
    parser.add_argument("--rambutan-image", type=Path)
    parser.add_argument("--live-gemini", action="store_true", help="call the real Gemini API instead of the stub")
    args = parser.parse_args()

    if not args.live_gemini:
        settings.GEMINI_API_KEY = "stub"
        current = {"crop": None}
        original = skill_service.diagnose_leaf

        def tracking(image_path, crop, diseases, user_id):
            current["crop"] = crop.code
            return original(image_path, crop, diseases, user_id)

        skill_service._call = lambda image, prompt, schema: STUB_ANSWERS.get(current["crop"], {"label": "unknown", "confidence": 0, "reason": ""})
        gemini_skill.diagnose_leaf = tracking  # type: ignore[assignment]
        import app.services.prediction_service as ps
        ps.gemini_skill.diagnose_leaf = tracking  # type: ignore[attr-defined]
    elif not settings.GEMINI_API_KEY:
        print("GEMINI_API_KEY is not set; cannot use --live-gemini")
        return 2
    weather_service.get_outlook = lambda lat, lng: WET_WEEK  # deterministic radar weather

    images = {
        "durian": args.durian_image or _placeholder_leaf(_TMP / "durian.jpg"),
        "mangosteen": args.mangosteen_image or _placeholder_leaf(_TMP / "mangosteen.jpg"),
        "rambutan": args.rambutan_image or _placeholder_leaf(_TMP / "rambutan.jpg"),
    }
    all_ok = True
    with TestClient(app) as client:
        headers_by_user = []
        for _ in range(2):  # two users so the radar's k-anonymity threshold (2 users per cell) is met
            pw = "E2e" + secrets.token_hex(6) + "!"
            reg = client.post("/api/auth/register", json={"email": f"e2e_{secrets.token_hex(4)}@leafai.dev", "password": pw, "password_confirmation": pw})
            headers_by_user.append({"Authorization": f"Bearer {reg.json()['access_token']}"})
        crops = {c["code"]: c for c in client.get("/api/crops").json()}
        print("crops:", {k: v["diagnosis_mode"] for k, v in crops.items()})
        for crop, image in images.items():
            for headers in headers_by_user:
                all_ok &= run_crop(client, headers, crop, image)
        print("\n== radar (durian, wet forecast)")
        radar = client.get("/api/radar", headers=headers_by_user[0], params={"lat": 10.24, "lng": 106.37, "radius_km": 5, "crop": "durian"})
        all_ok &= _check(radar.status_code == 200, f"radar HTTP {radar.status_code}")
        if radar.status_code == 200:
            for alert in radar.json().get("alerts", []):
                print(f"   - {alert['level']}: {alert['message'][:160]}")
    print("\nRESULT:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

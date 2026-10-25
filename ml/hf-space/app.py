# -*- coding: utf-8 -*-
"""
LEAF_AI — Máy chủ suy luận bệnh lá vải thiều Lục Ngạn (FastAPI, chạy trên Render / Hugging Face Space).

Thay đổi so với bản cũ:
  • Nạp mô hình LÁ VẢI huấn luyện bằng ml/training/train_lychee.py (lychee_model.pt).
    Không còn đổi tên lớp từ mô hình cà chua (TOMATO_TO_LYCHEE_MAP) — checkpoint cà chua bị từ chối.
  • Không còn "phân tích quang học dự phòng" trả % gán cứng. Mô hình chưa sẵn sàng → HTTP 503,
    frontend chuyển sang Gemini (ca khó) thay vì hiển thị kết quả bịa.
  • Trả cờ `uncertain` (dưới ngưỡng chấp nhận tính lúc train, hai lớp sát nhau, hoặc lớp "Other")
    để frontend hỏi thêm Gemini.

Biến môi trường:
  MODEL_PATH          đường dẫn checkpoint (mặc định ./lychee_model.pt)
  MODEL_DOWNLOAD_URL  URL tải checkpoint nếu chưa có file (vd https://huggingface.co/<user>/<repo>/resolve/main/lychee_model.pt)
  TORCH_THREADS       số luồng CPU cho PyTorch (mặc định 2)
"""
import base64
import io
import logging
import os
import re
import threading
import time
import urllib.request
from pathlib import Path
from typing import Optional

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from PIL import Image, ImageOps
from pydantic import BaseModel

from inference import CLASS_NAME_VI, LycheeClassifier, WrongModelError
from treatment import router as treatment_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("leaf_ai_service")
torch.set_num_threads(int(os.environ.get("TORCH_THREADS", "2")))

app = FastAPI(
    title="LEAF_AI — Lychee Leaf Disease Engine",
    description="Nhận diện bệnh lá vải thiều Lục Ngạn (CNN fine-tune + Grad-CAM) & phác đồ IPM",
    version="3.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
app.include_router(treatment_router)

APP_DIR = Path(__file__).parent
MODEL_PATH = Path(os.environ.get("MODEL_PATH", APP_DIR / "lychee_model.pt"))
MAX_IMAGE_BYTES = 8_000_000

classifier: Optional[LycheeClassifier] = None
model_state = {"status": "loading", "detail": "", "loaded_at": None}
_infer_lock = threading.Lock()   # Grad-CAM dùng hook trên model: tuần tự hoá để an toàn đa luồng


def load_model():
    global classifier
    try:
        if not MODEL_PATH.exists():
            url = os.environ.get("MODEL_DOWNLOAD_URL", "").strip()
            if not url:
                model_state.update(status="no_model", detail=f"Chưa có {MODEL_PATH.name} và chưa đặt MODEL_DOWNLOAD_URL")
                logger.warning(model_state["detail"])
                return
            logger.info(f"Đang tải mô hình từ {url} …")
            tmp = MODEL_PATH.with_suffix(".download")
            urllib.request.urlretrieve(url, str(tmp))
            tmp.replace(MODEL_PATH)
            logger.info(f"[OK] Đã tải {MODEL_PATH.stat().st_size / 1e6:.1f} MB")
        classifier = LycheeClassifier(str(MODEL_PATH), device="cpu")
        model_state.update(status="ready", detail="", loaded_at=time.strftime("%Y-%m-%d %H:%M:%S"))
    except WrongModelError as e:
        model_state.update(status="wrong_model", detail=str(e))
        logger.error(str(e))
    except Exception as e:  # noqa: BLE001
        model_state.update(status="error", detail=f"{e.__class__.__name__}: {e}")
        logger.exception("Lỗi nạp mô hình")


@app.on_event("startup")
def _startup():
    # Nạp nền để /health trả lời ngay (Render kiểm tra sức khoẻ trong lúc tải mô hình)
    threading.Thread(target=load_model, daemon=True).start()


class PredictRequest(BaseModel):
    data: str                            # data URL hoặc base64 ảnh lá
    model_version: Optional[str] = "v4"  # v4: trả top-3, v3: top-2 (tương thích frontend cũ)
    confidence: Optional[float] = None   # giữ để tương thích, không dùng
    heatmap: Optional[bool] = True


def decode_image(b64: str) -> Image.Image:
    m = re.match(r"^data:image/[\w.+-]+;base64,(.+)$", b64 or "", flags=re.DOTALL)
    raw = base64.b64decode(m.group(1) if m else b64, validate=False)
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("Ảnh quá lớn (> 8 MB)")
    img = Image.open(io.BytesIO(raw))
    return ImageOps.exif_transpose(img).convert("RGB")


def _require_model():
    if classifier is None:
        raise HTTPException(status_code=503, detail={"status": model_state["status"], "message": model_state["detail"] or "Mô hình đang khởi động"})


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "leaf_ai_lychee_engine",
        "model_status": model_state["status"],
        "model_detail": model_state["detail"],
        "metadata": classifier.meta if classifier else None,
        "supported_classes": classifier.classes if classifier else [],
        "features": ["predict_with_gradcam", "predict", "treatment_plan"],
    }


@app.post("/predict_with_gradcam")
def predict_with_gradcam(req: PredictRequest):
    _require_model()
    try:
        img = decode_image(req.data)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Không đọc được ảnh: {e}")
    top_k = 3 if (req.model_version or "v4") == "v4" else 2
    t0 = time.time()
    with _infer_lock:
        out = classifier.predict(img, with_heatmap=bool(req.heatmap), top_k=top_k)
    out["latency_ms"] = int((time.time() - t0) * 1000)
    return out


@app.post("/predict")
def predict_simple(req: PredictRequest):
    req.heatmap = False
    return predict_with_gradcam(req)


@app.get("/", response_class=HTMLResponse)
def index():
    meta = classifier.meta if classifier else {}
    classes = ", ".join(f"{c} ({CLASS_NAME_VI.get(c, c)})" for c in (classifier.classes if classifier else []))
    return f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>LEAF_AI Engine</title>
<style>body{{font-family:system-ui;max-width:760px;margin:40px auto;padding:0 16px;color:#12301f}}code{{background:#eef7eb;padding:2px 6px;border-radius:4px}}</style></head>
<body><h1>LEAF_AI — Lychee Leaf Disease Engine</h1>
<p>Trạng thái mô hình: <b>{model_state['status']}</b> {model_state['detail']}</p>
<p>Kiến trúc: <code>{meta.get('arch', '—')}</code> · Phiên bản: <code>{meta.get('version', '—')}</code> ·
Độ chính xác test: <code>{meta.get('best_acc', '—')}%</code> · Macro-F1: <code>{meta.get('test_macro_f1', '—')}%</code></p>
<p>Lớp: {classes or '—'}</p>
<p>API: <code>POST /predict_with_gradcam</code> {{"data": "data:image/jpeg;base64,..."}} · <code>GET /health</code> · <code>POST /treatment/plan</code></p>
</body></html>"""

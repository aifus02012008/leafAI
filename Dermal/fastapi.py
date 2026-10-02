import os
import logging
import requests

logger = logging.getLogger(__name__)

# AI server (FastAPI + YOLOv8) — override bằng env AI_SERVER_URL khi deploy
AI_SERVER_URL = os.getenv(
    "AI_SERVER_URL",
    "https://codedr-skin-detection-torch.hf.space/predict_with_gradcam",
)

# Model versions theo spec LEAF_AI
MODEL_V3 = "v3"  # production, 3 lớp bệnh (mặc định)
MODEL_V4 = "v4"  # experimental, 6 lớp bệnh
VALID_MODELS = (MODEL_V3, MODEL_V4)

DEFAULT_TIMEOUT = int(os.getenv("AI_SERVER_TIMEOUT", "60"))  # giây, tránh treo worker


class AIServerError(Exception):
    """Lỗi khi gọi AI server (network, timeout, response sai cấu trúc)."""


def fast_api(image_b64, model_version=MODEL_V3, confidence=0.25):
    """Gọi AI server để chẩn đoán ảnh lá cây.

    Trả về dict: {"results": [...], "heatmap_base64": str|None}
    Ném AIServerError nếu server lỗi / timeout / response sai cấu trúc.
    """
    if model_version not in VALID_MODELS:
        raise AIServerError(f"Model không hợp lệ: {model_version}")

    payload = {
        "data": image_b64,
        "model_version": model_version,
        "confidence": confidence,
    }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(
            AI_SERVER_URL, json=payload, headers=headers, timeout=DEFAULT_TIMEOUT
        )
    except requests.exceptions.Timeout as e:
        raise AIServerError(f"AI server quá thời gian chờ ({DEFAULT_TIMEOUT}s)") from e
    except requests.exceptions.RequestException as e:
        raise AIServerError(f"Không kết nối được AI server: {e}") from e

    if response.status_code != 200:
        raise AIServerError(
            f"AI server trả về HTTP {response.status_code}: {response.text[:200]}"
        )

    try:
        data = response.json()
    except ValueError as e:
        raise AIServerError("AI server trả về JSON không hợp lệ") from e

    # Response hợp lệ phải có 'results'
    if not isinstance(data, dict) or "results" not in data:
        raise AIServerError("AI server thiếu trường 'results' trong response")

    # heatmap là tùy chọn (một số model chưa có)
    if data.get("heatmap_base64") in (None, ""):
        data["heatmap_base64"] = None

    return data

"""Gemini Vision call + caching + per-user rate limiting for the leaf skill."""
from __future__ import annotations

import base64
import hashlib
import io
import json
import logging
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Sequence

import httpx
from PIL import Image, ImageOps

from app.core.config import settings
from app.core.crops import CropConfig
from app.core.rate_limit import hit
from app.services.gemini_skill.schema import GeminiLeafVerdict, parse_verdict, response_schema

logger = logging.getLogger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta"
MAX_SIDE_PX = 1024          # downscale before upload: faster, cheaper, enough detail for lesions
CACHE_SIZE = 256
SYSTEM_PROMPT = (
    "Bạn là chuyên gia bảo vệ thực vật. Nhiệm vụ: xem ảnh một chiếc lá và chọn đúng MỘT nhãn trong danh "
    "sách cho phép. Chỉ chọn tên bệnh khi thấy rõ triệu chứng khớp với mô tả; nếu lá khỏe chọn 'healthy'; "
    "nếu ảnh mờ, không phải lá của cây được chỉ định, hoặc triệu chứng không khớp bệnh nào thì chọn 'unknown'. "
    "confidence là mức chắc chắn từ 0 đến 1, đừng thổi phồng. box là vùng vết bệnh rõ nhất theo tọa độ chuẩn "
    "hóa 0..1 (để null nếu khỏe/unknown). reason: một câu tiếng Việt ngắn nêu dấu hiệu nhìn thấy."
)


class GeminiSkillError(RuntimeError):
    """Gemini is not configured, unreachable, overloaded or returned garbage."""


class GeminiSkillRateLimited(GeminiSkillError):
    """The user exceeded the per-minute Gemini Vision quota."""


_cache: "OrderedDict[str, GeminiLeafVerdict]" = OrderedDict()
_cache_lock = threading.Lock()


def reset_cache() -> None:
    with _cache_lock:
        _cache.clear()


def is_enabled() -> bool:
    return bool(settings.GEMINI_API_KEY) and settings.GEMINI_VISION_ENABLED


def _prepared_jpeg(image_path: str) -> bytes:
    with Image.open(image_path) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((MAX_SIDE_PX, MAX_SIDE_PX))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=88)
        return buf.getvalue()


def _prompt(crop: CropConfig, diseases: Sequence[dict]) -> str:
    catalogue = "\n".join(f"- {d['class_name']}: {(d.get('symptoms') or '')[:220]}" for d in diseases)
    return (
        f"Cây: {crop.name_vi} ({crop.scientific_name}).\n"
        f"Các bệnh cho phép (tên phải chép y nguyên):\n{catalogue}\n"
        "Trả về JSON theo schema."
    )


def _call(image: bytes, prompt: str, schema: dict) -> dict:
    try:
        res = httpx.post(
            f"{GEMINI_URL}/models/{settings.GEMINI_VISION_MODEL or settings.GEMINI_MODEL}:generateContent",
            headers={"x-goog-api-key": settings.GEMINI_API_KEY or "", "content-type": "application/json"},
            json={
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{
                    "role": "user",
                    "parts": [
                        {"inlineData": {"mimeType": "image/jpeg", "data": base64.b64encode(image).decode()}},
                        {"text": prompt},
                    ],
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "maxOutputTokens": 512,
                    "responseMimeType": "application/json",
                    "responseSchema": schema,
                },
            },
            timeout=settings.GEMINI_VISION_TIMEOUT_SECONDS,
        )
        res.raise_for_status()
        payload = res.json()
        parts = payload["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts if isinstance(p, dict) and not p.get("thought"))
        return json.loads(text)
    except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
        # Log type/status only: the request object carries the API key header.
        status = getattr(getattr(exc, "response", None), "status_code", None)
        logger.warning("Gemini leaf skill call failed (%s %s)", type(exc).__name__, status)
        raise GeminiSkillError("Gemini Vision is unavailable") from exc


def diagnose_leaf(image_path: str, crop: CropConfig, diseases: Sequence[dict], user_id: int) -> GeminiLeafVerdict:
    """Classify a leaf photo into one of ``diseases`` (dicts with class_name/symptoms), 'healthy' or 'unknown'.

    Raises GeminiSkillError (not configured / API failure) or GeminiSkillRateLimited.
    """
    if not is_enabled():
        raise GeminiSkillError("Gemini Vision is not configured")
    image = _prepared_jpeg(image_path)
    names = [d["class_name"] for d in diseases]
    key = f"{crop.code}:{hashlib.sha256(image).hexdigest()}"
    with _cache_lock:
        if key in _cache:
            _cache.move_to_end(key)
            return _cache[key]
    if not hit(f"gemini-vision:{user_id}", settings.GEMINI_VISION_PER_MINUTE):
        raise GeminiSkillRateLimited("Too many Gemini Vision requests")
    verdict = parse_verdict(_call(image, _prompt(crop, diseases), response_schema(names)), names)
    with _cache_lock:
        _cache[key] = verdict
        while len(_cache) > CACHE_SIZE:
            _cache.popitem(last=False)
    return verdict


def image_size(image_path: str) -> tuple[int, int]:
    with Image.open(Path(image_path)) as img:
        return ImageOps.exif_transpose(img).size

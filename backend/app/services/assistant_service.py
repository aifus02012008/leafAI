"""Vietnamese Q&A assistant grounded in LEAF_AI's disease library.

1. Retrieve the most relevant diseases by keyword overlap (accent-insensitive).
2. If ANTHROPIC_API_KEY is configured, ask Claude to answer ONLY from that context.
3. Otherwise (or on any API error) fall back to a deterministic answer built from the library.
Doses are never generated: the assistant points users to the product label.
"""
from __future__ import annotations

import logging
import re
import threading
import time
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.crops import list_crops
from app.models.disease import Disease

logger = logging.getLogger(__name__)

RATE_LIMIT_PER_MINUTE = 10
MAX_CONTEXTS = 3
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
DISCLAIMER = "Lưu ý: dùng đúng liều trên nhãn thuốc và tham vấn cán bộ BVTV địa phương trước khi áp dụng."
STOPWORDS = frozenset(
    "la bi co cua va thi phai lam sao gi nao nhu the nay khi toi em anh chi cay benh duoc cho voi "
    "o tren duoi mot nhung cac rat qua hay hoi bao lau the nao".split()
)
SYSTEM_PROMPT = (
    "Bạn là trợ lý nông nghiệp của ứng dụng LEAF_AI, trả lời nông dân Việt Nam (nhiều người lớn tuổi). "
    "Quy tắc: (1) Chỉ dùng thông tin trong phần TÀI LIỆU; nếu không có, nói rõ là chưa có thông tin và "
    "khuyên chụp ảnh lá để chẩn đoán hoặc hỏi cán bộ BVTV. (2) KHÔNG BAO GIỜ tự đưa ra liều lượng, nồng độ "
    "hay thời gian cách ly cụ thể — hướng dẫn người dùng đọc nhãn thuốc. (3) Trả lời bằng tiếng Việt, câu "
    "ngắn, dễ hiểu, tối đa khoảng 120 chữ, không dùng markdown vì câu trả lời sẽ được đọc thành tiếng."
)


class RateLimitError(Exception):
    pass


@dataclass(frozen=True)
class ContextHit:
    id: int
    crop_code: str
    class_name: str
    symptoms: str
    treatment: str
    score: float


@dataclass(frozen=True)
class AssistantAnswer:
    answer: str
    source: str  # "ai" | "library"
    related: tuple[ContextHit, ...]


# ---------- rate limiting (in-memory, per process) ----------

_calls: dict[int, deque] = defaultdict(deque)
_calls_lock = threading.Lock()


def reset_rate_limits() -> None:
    with _calls_lock:
        _calls.clear()


def _check_rate_limit(user_id: int) -> None:
    now = time.monotonic()
    with _calls_lock:
        window = _calls[user_id]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= RATE_LIMIT_PER_MINUTE:
            raise RateLimitError
        window.append(now)


# ---------- retrieval ----------

def _fold(text: str) -> str:
    text = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", _fold(text)) if len(t) >= 2 and t not in STOPWORDS]


def _crop_in_question(question: str) -> str | None:
    folded = _fold(question)
    for crop in list_crops():
        if re.search(rf"\b{re.escape(_fold(crop.name_vi))}\b", folded):
            return crop.code
    return None


def _words(text: str | None) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", _fold(text or "")))


def _score(tokens: list[str], disease: Disease) -> float:
    name = _words(disease.class_name)
    body = _words(disease.symptoms) | _words(disease.description)
    return sum(3.0 if tok in name else (1.0 if tok in body else 0.0) for tok in tokens)


def retrieve_context(db: Session, question: str, crop_code: str | None) -> list[ContextHit]:
    crop = crop_code or _crop_in_question(question)
    query = db.query(Disease)
    if crop:
        query = query.filter(Disease.crop_code == crop)
    tokens = _tokens(question)
    scored = sorted(
        ((_score(tokens, d), d) for d in query.all()),
        key=lambda pair: pair[0],
        reverse=True,
    )
    return [
        ContextHit(d.id, d.crop_code, d.class_name, d.symptoms or "", d.treatment or "", s)
        for s, d in scored[:MAX_CONTEXTS]
        if s > 0
    ]


# ---------- answering ----------

def _first_sentences(text: str, n: int) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(parts[:n]).strip()


def _library_answer(hits: list[ContextHit]) -> str:
    if not hits:
        return (
            "Mình chưa tìm thấy thông tin phù hợp trong thư viện. Bác hãy chụp ảnh lá bệnh "
            "để LEAF AI chẩn đoán, hoặc hỏi cán bộ bảo vệ thực vật địa phương."
        )
    top = hits[0]
    return (
        f"Có thể là bệnh {top.class_name}. Dấu hiệu: {_first_sentences(top.symptoms, 2)} "
        f"Cách xử lý: {_first_sentences(top.treatment, 2)}"
    )


def _llm_answer(question: str, contexts: list[ContextHit]) -> str | None:
    """Ask Claude; returns None when not configured or on any failure (caller falls back)."""
    if not settings.ANTHROPIC_API_KEY:
        return None
    docs = "\n\n".join(
        f"[{i + 1}] {c.class_name}\nTriệu chứng: {c.symptoms}\nXử lý: {c.treatment}" for i, c in enumerate(contexts)
    ) or "(không có tài liệu phù hợp)"
    try:
        res = httpx.post(
            ANTHROPIC_URL,
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.ASSISTANT_MODEL,
                "max_tokens": 500,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": f"TÀI LIỆU:\n{docs}\n\nCÂU HỎI: {question}"}],
            },
            timeout=30.0,
        )
        res.raise_for_status()
        payload = res.json()
        blocks = payload.get("content", []) if isinstance(payload, dict) else []
        text = "".join(
            b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"
        ).strip()
        return text or None
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Assistant LLM call failed, falling back to library answer: %s", exc)
        return None


def answer_question(db: Session, user_id: int, question: str, crop_code: str | None) -> AssistantAnswer:
    _check_rate_limit(user_id)
    hits = retrieve_context(db, question, crop_code)
    ai_text = _llm_answer(question, hits)
    if ai_text:
        return AssistantAnswer(f"{ai_text}\n{DISCLAIMER}", "ai", tuple(hits))
    return AssistantAnswer(f"{_library_answer(hits)}\n{DISCLAIMER}", "library", tuple(hits))

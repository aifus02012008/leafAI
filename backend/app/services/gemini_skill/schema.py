"""Structured-output contract for the Gemini leaf skill (pure: no I/O)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Sequence

Status = Literal["diseased", "healthy", "unknown"]
HEALTHY = "healthy"
UNKNOWN = "unknown"
MAX_REASON_CHARS = 300


@dataclass(frozen=True)
class GeminiLeafVerdict:
    status: Status
    disease: str | None          # exact class_name from the crop's library when status == "diseased"
    confidence: float            # 0..1
    box: tuple[float, float, float, float] | None  # normalised x1, y1, x2, y2 in 0..1
    reason: str


def response_schema(disease_names: Sequence[str]) -> dict[str, Any]:
    """Gemini responseSchema: the label must be one of the library names, 'healthy' or 'unknown'."""
    return {
        "type": "OBJECT",
        "properties": {
            "label": {"type": "STRING", "enum": [*disease_names, HEALTHY, UNKNOWN]},
            "confidence": {"type": "NUMBER"},
            "box": {
                "type": "OBJECT",
                "nullable": True,
                "properties": {k: {"type": "NUMBER"} for k in ("x1", "y1", "x2", "y2")},
                "required": ["x1", "y1", "x2", "y2"],
            },
            "reason": {"type": "STRING"},
        },
        "required": ["label", "confidence", "reason"],
    }


def _clamp01(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return min(1.0, max(0.0, number))


def _parse_box(raw: Any) -> tuple[float, float, float, float] | None:
    if not isinstance(raw, dict):
        return None
    coords = [_clamp01(raw.get(k)) for k in ("x1", "y1", "x2", "y2")]
    if any(c is None for c in coords):
        return None
    x1, y1, x2, y2 = coords  # type: ignore[misc]
    x1, x2 = sorted((x1, x2))
    y1, y2 = sorted((y1, y2))
    if x2 - x1 < 0.02 or y2 - y1 < 0.02:  # degenerate box
        return None
    return (x1, y1, x2, y2)


def parse_verdict(payload: Any, disease_names: Sequence[str]) -> GeminiLeafVerdict:
    """Validate Gemini's JSON. Anything outside the contract degrades to an 'unknown' verdict."""
    if not isinstance(payload, dict):
        return GeminiLeafVerdict(UNKNOWN, None, 0.0, None, "Phản hồi không hợp lệ.")
    label = str(payload.get("label", "")).strip()
    confidence = _clamp01(payload.get("confidence")) or 0.0
    reason = str(payload.get("reason", "")).strip()[:MAX_REASON_CHARS]
    if label in disease_names:
        return GeminiLeafVerdict("diseased", label, confidence, _parse_box(payload.get("box")), reason)
    if label == HEALTHY:
        return GeminiLeafVerdict("healthy", None, confidence, None, reason)
    return GeminiLeafVerdict(UNKNOWN, None, confidence, None, reason)

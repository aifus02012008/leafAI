"""Crop-aware post-processing of raw model detections.

Pure functions only: no I/O, no model, no database. This keeps the clinical
decision logic (thresholds, healthy-vs-disease arbitration) easy to unit test.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from app.core.crops import CropConfig

# When the model also sees healthy tissue, prefer "healthy" if it is at least as
# confident as the disease, or clearly healthy while the disease signal is faint.
HEALTHY_DOMINANT_CONF = 0.50
FAINT_DISEASE_CONF = 0.45


@dataclass(frozen=True)
class RawDetection:
    label: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True)
class DetectionOutcome:
    status: str
    detections: tuple[dict, ...] = field(default_factory=tuple)
    healthy_confidence: float | None = None
    unclear_disease_suppressed: bool = False


def _to_record(det: RawDetection, class_name: str) -> dict:
    return {
        "class_name": class_name,
        "confidence": round(det.confidence, 4),
        "x1": round(det.x1, 2),
        "y1": round(det.y1, 2),
        "x2": round(det.x2, 2),
        "y2": round(det.y2, 2),
    }


def _split(raw: Iterable[RawDetection], crop: CropConfig) -> tuple[list[dict], list[dict]]:
    healthy: list[dict] = []
    disease: list[dict] = []
    for det in raw:
        if crop.is_healthy_label(det.label):
            if det.confidence >= crop.healthy_threshold:
                healthy.append(_to_record(det, "Healthy"))
            continue
        if det.confidence < crop.threshold_for(det.label):
            continue
        disease.append(_to_record(det, crop.map_label(det.label)))
    return healthy, disease


def _healthy_wins(max_healthy: float, max_disease: float) -> bool:
    if max_healthy <= 0:
        return False
    return max_healthy >= max_disease or (
        max_healthy >= HEALTHY_DOMINANT_CONF and max_disease < FAINT_DISEASE_CONF
    )


def evaluate_detections(raw: Iterable[RawDetection], crop: CropConfig) -> DetectionOutcome:
    """Filter raw detections by crop thresholds and decide healthy vs. diseased."""
    healthy, disease = _split(raw, crop)
    max_healthy = max((b["confidence"] for b in healthy), default=0.0)
    max_disease = max((b["confidence"] for b in disease), default=0.0)
    healthy_conf = round(max_healthy, 4) if max_healthy > 0 else None

    if not disease:
        return DetectionOutcome(status="no_detection", healthy_confidence=healthy_conf)
    if _healthy_wins(max_healthy, max_disease):
        return DetectionOutcome(
            status="no_detection",
            healthy_confidence=healthy_conf,
            unclear_disease_suppressed=True,
        )
    return DetectionOutcome(
        status="detected",
        detections=tuple(disease),
        healthy_confidence=healthy_conf,
    )

"""Convert ORM diagnosis records into API response objects (crop-aware label mapping)."""
from __future__ import annotations

from app.core.crops import CropConfig, CropNotFoundError, get_crop
from app.models.detection import DetectionResult
from app.models.diagnosis import DiagnosisHistory
from app.schemas.diagnosis import DetectionResponse, DiagnosisListResponse, DiagnosisResponse


def _crop_or_none(code: str | None) -> CropConfig | None:
    try:
        return get_crop(code or "tea")
    except CropNotFoundError:
        return None


def map_for_crop(crop_code: str | None, class_name: str) -> str:
    """Stored labels are canonical already; re-mapping keeps legacy raw tea labels readable."""
    crop = _crop_or_none(crop_code)
    return crop.map_label(class_name) if crop else class_name


def display_label(record: DiagnosisHistory, class_name: str) -> str:
    return map_for_crop(record.crop_code, class_name)


def _top_detection(record: DiagnosisHistory) -> DetectionResult | None:
    return max(record.detections, key=lambda d: d.confidence) if record.detections else None


def _image_url(path: str | None) -> str | None:
    return f"/api/images/{path}" if path else None


def to_detection_responses(record: DiagnosisHistory) -> list[DetectionResponse]:
    return [
        DetectionResponse(
            id=d.id,
            class_name=display_label(record, d.class_name),
            confidence=d.confidence,
            x1=d.x1,
            y1=d.y1,
            x2=d.x2,
            y2=d.y2,
        )
        for d in record.detections
    ]


def to_diagnosis_response(record: DiagnosisHistory) -> DiagnosisResponse:
    return DiagnosisResponse(
        id=record.id,
        crop_code=record.crop_code,
        model_version=record.model_version,
        original_image_url=_image_url(record.original_image_path) or "",
        result_image_url=_image_url(record.result_image_path),
        status=record.status,
        inference_time=record.inference_time,
        created_at=record.created_at,
        detections=to_detection_responses(record),
        user_feedback=record.user_feedback,
        severity_pct=record.severity_pct,
    )


def to_list_item(record: DiagnosisHistory) -> DiagnosisListResponse:
    best = _top_detection(record)
    return DiagnosisListResponse(
        id=record.id,
        crop_code=record.crop_code,
        original_image_url=_image_url(record.original_image_path) or "",
        result_image_url=_image_url(record.result_image_path),
        status=record.status,
        inference_time=record.inference_time,
        created_at=record.created_at,
        detection_count=len(record.detections),
        primary_disease=display_label(record, best.class_name) if best else None,
        max_confidence=best.confidence if best else None,
        user_feedback=record.user_feedback,
    )

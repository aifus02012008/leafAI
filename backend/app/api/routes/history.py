from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.history_service import get_user_history, get_diagnosis_detail, delete_diagnosis
from app.schemas.diagnosis import DiagnosisResponse, DiagnosisListResponse, DetectionResponse
from app.core.config import map_disease_label

router = APIRouter(prefix="/api/history", tags=["History"])

@router.get("", response_model=list[DiagnosisListResponse])
def list_history(
    status: str | None = Query(None),
    search: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    records = get_user_history(current_user.id, db, status_filter=status, search=search)
    results = []
    for rec in records:
        primary_disease = None
        max_conf = None
        if rec.detections:
            best = max(rec.detections, key=lambda d: d.confidence)
            primary_disease = map_disease_label(best.class_name)
            max_conf = best.confidence
            
        results.append(DiagnosisListResponse(
            id=rec.id,
            original_image_url=f"/api/images/{rec.original_image_path}",
            result_image_url=f"/api/images/{rec.result_image_path}" if rec.result_image_path else None,
            status=rec.status,
            inference_time=rec.inference_time,
            created_at=rec.created_at,
            detection_count=len(rec.detections),
            primary_disease=primary_disease,
            max_confidence=max_conf
        ))
    return results

@router.get("/{history_id}", response_model=DiagnosisResponse)
def get_history_item(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rec = get_diagnosis_detail(history_id, current_user.id, db)
    return DiagnosisResponse(
        id=rec.id,
        original_image_url=f"/api/images/{rec.original_image_path}",
        result_image_url=f"/api/images/{rec.result_image_path}" if rec.result_image_path else None,
        status=rec.status,
        inference_time=rec.inference_time,
        created_at=rec.created_at,
        detections=[
            DetectionResponse(
                id=d.id,
                class_name=map_disease_label(d.class_name),
                confidence=d.confidence,
                x1=d.x1,
                y1=d.y1,
                x2=d.x2,
                y2=d.y2
            )
            for d in rec.detections
        ]
    )

@router.delete("/{history_id}")
def delete_history_item(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return delete_diagnosis(history_id, current_user.id, db)

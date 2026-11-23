from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status
from app.models.diagnosis import DiagnosisHistory
from app.models.detection import DetectionResult
import logging
from datetime import datetime, timezone
from app.services.storage import LocalStorage, StorageError, get_storage

logger = logging.getLogger(__name__)

def get_user_history(
    user_id: int,
    db: Session,
    status_filter: str | None = None,
    search: str | None = None,
    crop_code: str | None = None
) -> list[DiagnosisHistory]:
    """Retrieve history records strictly owned by the authenticated user."""
    query = db.query(DiagnosisHistory).filter(DiagnosisHistory.user_id == user_id)

    if crop_code:
        query = query.filter(DiagnosisHistory.crop_code == crop_code)
    
    if status_filter and status_filter != "all":
        query = query.filter(DiagnosisHistory.status == status_filter)
        
    if search and search.strip():
        term = f"%{search.strip()}%"
        # Search either in status or in associated detection class names
        query = query.filter(
            DiagnosisHistory.detections.any(DetectionResult.class_name.ilike(term))
        )
        
    return query.order_by(desc(DiagnosisHistory.created_at)).all()

def set_feedback(history_id: int, user_id: int, feedback: str, db: Session) -> DiagnosisHistory:
    """Record the user's verdict on a diagnosis (ownership enforced)."""
    rec = get_diagnosis_detail(history_id, user_id, db)
    rec.user_feedback = feedback
    rec.feedback_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(rec)
    return rec

def get_diagnosis_detail(history_id: int, user_id: int, db: Session) -> DiagnosisHistory:
    """Retrieve diagnosis record with strict ownership check."""
    rec = db.query(DiagnosisHistory).filter(
        DiagnosisHistory.id == history_id,
        DiagnosisHistory.user_id == user_id
    ).first()
    
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnosis record not found or access denied"
        )
    return rec

def _delete_images(keys: list[str | None]) -> None:
    local = LocalStorage()
    remote = get_storage()
    for key in filter(None, keys):
        local.delete(key)
        if not isinstance(remote, LocalStorage):
            try:
                remote.delete(key)
            except StorageError as exc:
                logger.warning("Remote image delete failed for %s: %s", key, exc)


def delete_diagnosis(history_id: int, user_id: int, db: Session) -> dict:
    """Delete diagnosis record with strict ownership check and clean up image files."""
    rec = db.query(DiagnosisHistory).filter(
        DiagnosisHistory.id == history_id,
        DiagnosisHistory.user_id == user_id
    ).first()
    
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnosis record not found or access denied"
        )
        
    # Delete image files locally and in the remote store (if configured).
    _delete_images([rec.original_image_path, rec.result_image_path])

    db.delete(rec)
    db.commit()
    return {"message": "Diagnosis record deleted successfully", "id": history_id}

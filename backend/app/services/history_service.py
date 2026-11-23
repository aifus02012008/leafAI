from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import desc
from fastapi import HTTPException, status
from app.models.diagnosis import DiagnosisHistory
from app.models.detection import DetectionResult
from app.core.config import settings
from pathlib import Path
from datetime import datetime, timezone
import os

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
        
    # Delete image files on disk safely
    storage_root = settings.storage_dir
    if rec.original_image_path:
        p = (storage_root / rec.original_image_path).resolve()
        if p.exists() and storage_root in p.parents:
            try:
                os.remove(str(p))
            except Exception:
                pass
                
    if rec.result_image_path:
        p = (storage_root / rec.result_image_path).resolve()
        if p.exists() and storage_root in p.parents:
            try:
                os.remove(str(p))
            except Exception:
                pass
                
    db.delete(rec)
    db.commit()
    return {"message": "Diagnosis record deleted successfully", "id": history_id}

from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.dependencies import optional_crop_filter
from app.api.presenters import to_diagnosis_response, to_list_item
from app.core.crops import CropConfig
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.diagnosis import (
    DiagnosisListResponse,
    DiagnosisResponse,
    FeedbackRequest,
    FeedbackResponse,
)
from app.services.history_service import (
    delete_diagnosis,
    get_diagnosis_detail,
    get_user_history,
    set_feedback,
)

router = APIRouter(prefix="/api/history", tags=["History"])

@router.get("", response_model=list[DiagnosisListResponse])
def list_history(
    status: str | None = Query(None, max_length=32),
    search: str | None = Query(None, max_length=100),
    crop: CropConfig | None = Depends(optional_crop_filter),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    records = get_user_history(
        current_user.id,
        db,
        status_filter=status,
        search=search,
        crop_code=crop.code if crop else None,
    )
    return [to_list_item(rec) for rec in records]

@router.get("/{history_id}", response_model=DiagnosisResponse)
def get_history_item(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return to_diagnosis_response(get_diagnosis_detail(history_id, current_user.id, db))

@router.post("/{history_id}/feedback", response_model=FeedbackResponse)
def submit_feedback(
    history_id: int,
    payload: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Người dùng xác nhận kết quả chẩn đoán đúng/sai — dữ liệu để cải thiện model."""
    rec = set_feedback(history_id, current_user.id, payload.feedback, db)
    return FeedbackResponse(id=rec.id, user_feedback=rec.user_feedback, feedback_at=rec.feedback_at)

@router.delete("/{history_id}")
def delete_history_item(
    history_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return delete_diagnosis(history_id, current_user.id, db)

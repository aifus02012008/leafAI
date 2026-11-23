from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.treatment import (
    EfficacyRow,
    FollowupCreate,
    FollowupResult,
    TreatmentCreate,
    TreatmentResponse,
)
from app.services import treatment_service as svc
from app.services.treatment_service import MIN_EFFICACY_SAMPLES

router = APIRouter(prefix="/api/treatments", tags=["Treatments"])


@router.get("/stats/efficacy", response_model=list[EfficacyRow])
def efficacy(
    min_samples: int = Query(MIN_EFFICACY_SAMPLES, ge=MIN_EFFICACY_SAMPLES, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hiệu quả thực tế theo hoạt chất × bệnh (dữ liệu gộp, ẩn danh)."""
    return svc.efficacy_stats(db, min_samples)


@router.get("", response_model=list[TreatmentResponse])
def list_treatments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return [svc.to_treatment_response(t, db) for t in svc.list_treatments(db, current_user.id)]


@router.post("", response_model=TreatmentResponse, status_code=status.HTTP_201_CREATED)
def create_treatment(
    payload: TreatmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return svc.to_treatment_response(svc.create_treatment(db, current_user.id, payload), db)


@router.get("/{treatment_id}", response_model=TreatmentResponse)
def get_treatment(treatment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.to_treatment_response(svc.get_treatment(db, current_user.id, treatment_id), db)


@router.delete("/{treatment_id}")
def delete_treatment(treatment_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc.delete_treatment(db, current_user.id, treatment_id)
    return {"message": "Đã xóa lần điều trị.", "id": treatment_id}


@router.post("/{treatment_id}/followups", response_model=FollowupResult, status_code=status.HTTP_201_CREATED)
def add_followup(
    treatment_id: int,
    payload: FollowupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return svc.add_followup(db, current_user.id, treatment_id, payload.diagnosis_id)

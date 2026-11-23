from __future__ import annotations
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.api.dependencies import optional_crop_filter
from app.core.crops import CropConfig
from app.db.session import get_db
from app.services.disease_service import get_all_diseases, get_disease_by_id
from app.schemas.disease import DiseaseResponse

router = APIRouter(prefix="/api/diseases", tags=["Disease Library"])

@router.get("", response_model=list[DiseaseResponse])
def list_diseases(
    search: str | None = Query(None, max_length=100),
    crop: CropConfig | None = Depends(optional_crop_filter),
    db: Session = Depends(get_db)
):
    return get_all_diseases(db, search=search, crop_code=crop.code if crop else None)

@router.get("/{disease_id}", response_model=DiseaseResponse)
def get_disease(
    disease_id: int,
    db: Session = Depends(get_db)
):
    disease = get_disease_by_id(disease_id, db)
    if not disease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disease with ID {disease_id} not found."
        )
    return disease

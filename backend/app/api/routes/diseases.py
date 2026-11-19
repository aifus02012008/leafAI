from __future__ import annotations
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.disease_service import get_all_diseases, get_disease_by_id
from app.schemas.disease import DiseaseResponse, DiseaseListResponse

router = APIRouter(prefix="/api/diseases", tags=["Disease Library"])

@router.get("", response_model=list[DiseaseResponse])
def list_diseases(
    search: str | None = Query(None),
    db: Session = Depends(get_db)
):
    return get_all_diseases(db, search=search)

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

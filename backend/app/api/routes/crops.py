from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.crops import list_crops
from app.db.session import get_db
from app.models.disease import Disease
from app.schemas.crop import CropResponse
from app.services.model_registry import model_registry

router = APIRouter(prefix="/api/crops", tags=["Crops"])


@router.get("", response_model=list[CropResponse])
def get_crops(db: Session = Depends(get_db)):
    """Supported crops, whether their diagnosis model is available, and library size."""
    counts = dict(
        db.query(Disease.crop_code, func.count(Disease.id)).group_by(Disease.crop_code).all()
    )
    return [
        CropResponse(
            code=crop.code,
            name_vi=crop.name_vi,
            name_en=crop.name_en,
            scientific_name=crop.scientific_name,
            is_available=model_registry.is_available(crop),
            model_version=crop.model_version,
            disease_count=counts.get(crop.code, 0),
        )
        for crop in list_crops()
    ]

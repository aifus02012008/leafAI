"""Grower tools: active-ingredient catalog, spray dose calculator, pre-harvest interval."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import optional_crop_filter
from app.core.crops import CropConfig
from app.db.seed.actives import ACTIVE_INGREDIENTS, actives_for_disease
from app.schemas.treatment import (
    ActiveResponse,
    DoseRequest,
    DoseResponse,
    HarvestRequest,
    HarvestResponse,
)
from app.services.dose_calculator import DoseInput, DoseInputError, calculate_dose
from app.services.treatment_rules import SprayRecord, harvest_safe_date
from app.services.treatment_service import to_active_response

router = APIRouter(prefix="/api", tags=["Tools"])


@router.get("/actives", response_model=list[ActiveResponse])
def list_actives(
    crop: CropConfig | None = Depends(optional_crop_filter),
    disease: str | None = Query(None, max_length=200),
):
    """All actives; those recommended for (crop, disease) come first. Banned ones are flagged."""
    recommended = actives_for_disease(crop.code, disease) if crop and disease else []
    rec_codes = {a["code"] for a in recommended}
    others = [a for a in ACTIVE_INGREDIENTS if a["code"] not in rec_codes]
    return [to_active_response(a, True) for a in recommended] + [to_active_response(a) for a in others]


@router.post("/tools/dose", response_model=DoseResponse)
def dose(payload: DoseRequest):
    try:
        result = calculate_dose(DoseInput(**payload.model_dump()))
    except DoseInputError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    return DoseResponse(**result.__dict__)


@router.post("/tools/harvest-date", response_model=HarvestResponse)
def harvest_date(payload: HarvestRequest):
    safe_on = harvest_safe_date(SprayRecord(s.applied_on, s.phi_days) for s in payload.sprays)
    remaining = max(0, (safe_on - date.today()).days) if safe_on else None
    return HarvestResponse(harvest_safe_on=safe_on, days_remaining=remaining)

from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

MIN_DATE = date(2000, 1, 1)
MAX_DATE = date(2100, 12, 31)


def _bounded(value: date | None) -> date | None:
    if value is not None and not (MIN_DATE <= value <= MAX_DATE):
        raise ValueError("Ngày không hợp lệ.")
    return value


class ActiveResponse(BaseModel):
    code: str
    name: str
    kind: str
    moa_scheme: str
    moa_code: Optional[str] = None
    banned: bool = False
    note: Optional[str] = None
    recommended: bool = False


# ---------- calculators ----------

class DoseRequest(BaseModel):
    area: float = Field(gt=0, le=10_000_000)
    area_unit: str = Field(max_length=20)
    tank_l: float = Field(gt=0, le=1000)
    label_dose: float = Field(gt=0, le=100_000)
    label_dose_basis: Literal["per_tank", "per_ha"]
    label_tank_l: Optional[float] = Field(default=None, gt=0, le=1000)
    water_l_per_ha: float = Field(gt=0, le=10_000)
    pack_size: Optional[float] = Field(default=None, gt=0, le=1_000_000)
    pack_price: Optional[float] = Field(default=None, gt=0, le=1_000_000_000)


class DoseResponse(BaseModel):
    area_m2: float
    total_water_l: float
    tanks_needed: int
    product_per_tank: float
    total_product: float
    packs_needed: Optional[int] = None
    estimated_cost: Optional[float] = None


class SprayIn(BaseModel):
    applied_on: date
    phi_days: int = Field(ge=0, le=365)

    _check_date = field_validator("applied_on")(_bounded)


class HarvestRequest(BaseModel):
    sprays: list[SprayIn] = Field(min_length=1, max_length=50)


class HarvestResponse(BaseModel):
    harvest_safe_on: Optional[date] = None
    days_remaining: Optional[int] = None


# ---------- treatments ----------

class TreatmentCreate(BaseModel):
    diagnosis_id: int
    active_code: str = Field(min_length=1, max_length=64)
    product_name: Optional[str] = Field(default=None, max_length=200)
    disease_name: Optional[str] = Field(default=None, max_length=200)
    applied_on: Optional[date] = None
    phi_days: Optional[int] = Field(default=None, ge=0, le=365)
    followup_days: int = Field(default=4, ge=3, le=7)
    area_m2: Optional[float] = Field(default=None, gt=0, le=10_000_000)
    total_product: Optional[float] = Field(default=None, ge=0, le=10_000_000)
    estimated_cost: Optional[float] = Field(default=None, ge=0, le=10_000_000_000)

    _check_date = field_validator("applied_on")(_bounded)


class FollowupCreate(BaseModel):
    diagnosis_id: int


class FollowupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    diagnosis_id: Optional[int] = None
    severity_after: Optional[float] = None
    relative_change: Optional[float] = None
    verdict: str
    created_at: datetime


class FollowupResult(FollowupResponse):
    severity_before: Optional[float] = None
    message: str
    checklist: list[str] = []
    rotation_suggestions: list[ActiveResponse] = []


class TreatmentResponse(BaseModel):
    id: int
    diagnosis_id: Optional[int] = None
    crop_code: str
    disease_name: Optional[str] = None
    active_code: str
    active_name: str
    moa_code: Optional[str] = None
    product_name: Optional[str] = None
    applied_on: date
    phi_days: Optional[int] = None
    harvest_safe_on: Optional[date] = None
    followup_due_on: date
    area_m2: Optional[float] = None
    total_product: Optional[float] = None
    estimated_cost: Optional[float] = None
    severity_before: Optional[float] = None
    status: str
    original_image_url: Optional[str] = None
    followups: list[FollowupResponse] = []
    created_at: datetime


class EfficacyRow(BaseModel):
    crop_code: str
    disease_name: Optional[str] = None
    active_code: str
    active_name: str
    samples: int
    effective: int
    effective_rate: float

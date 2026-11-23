"""Treatment log: record sprays, schedule re-photos, judge before/after, aggregate efficacy."""
from __future__ import annotations

from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.db.seed.actives import ACTIVES_BY_CODE, actives_for_disease
from app.models.diagnosis import DiagnosisHistory
from app.models.disease import Disease
from app.models.treatment import Treatment, TreatmentFollowup
from app.schemas.treatment import (
    ActiveResponse,
    EfficacyRow,
    FollowupResponse,
    FollowupResult,
    TreatmentCreate,
    TreatmentResponse,
)
from app.services.treatment_rules import SprayRecord, evaluate_response, harvest_safe_date, suggest_rotation
from app.api.presenters import display_label


# Aggregates below this many treatments are never published (anonymity + statistical noise).
MIN_EFFICACY_SAMPLES = 5


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy {what} hoặc không có quyền truy cập.")


def _unprocessable(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)


def _owned_diagnosis(db: Session, diagnosis_id: int, user_id: int) -> DiagnosisHistory:
    rec = db.query(DiagnosisHistory).filter(
        DiagnosisHistory.id == diagnosis_id, DiagnosisHistory.user_id == user_id
    ).first()
    if rec is None:
        raise _not_found("bản ghi chẩn đoán")
    return rec


def _owned_treatment(db: Session, treatment_id: int, user_id: int) -> Treatment:
    rec = db.query(Treatment).filter(Treatment.id == treatment_id, Treatment.user_id == user_id).first()
    if rec is None:
        raise _not_found("lần điều trị")
    return rec


def _usable_active(code: str) -> dict:
    active = ACTIVES_BY_CODE.get(code)
    if active is None:
        raise _unprocessable(f"Hoạt chất không có trong danh mục: '{code}'.")
    if active["banned"]:
        raise _unprocessable(f"Hoạt chất {active['name']} đã bị cấm sử dụng tại Việt Nam. Vui lòng chọn hoạt chất khác.")
    return active


def _top_disease(diag: DiagnosisHistory) -> str | None:
    if not diag.detections:
        return None
    best = max(diag.detections, key=lambda d: d.confidence)
    return display_label(diag, best.class_name)


def _library_disease(db: Session, crop_code: str, name: str | None) -> str | None:
    """Only accept disease names that exist in the library for this crop (no free text)."""
    if not name:
        return None
    exists = db.query(Disease.id).filter(Disease.crop_code == crop_code, Disease.class_name == name).first()
    return name if exists else None


def to_active_response(active: dict, recommended: bool = False) -> ActiveResponse:
    return ActiveResponse(**active, recommended=recommended)


def to_treatment_response(tr: Treatment, db: Session) -> TreatmentResponse:
    active = ACTIVES_BY_CODE.get(tr.active_code, {"name": tr.active_code, "moa_code": None})
    diag = db.get(DiagnosisHistory, tr.diagnosis_id) if tr.diagnosis_id else None
    harvest = harvest_safe_date([SprayRecord(tr.applied_on, tr.phi_days)])
    return TreatmentResponse(
        id=tr.id,
        diagnosis_id=tr.diagnosis_id,
        crop_code=tr.crop_code,
        disease_name=tr.disease_name,
        active_code=tr.active_code,
        active_name=active["name"],
        moa_code=active.get("moa_code"),
        product_name=tr.product_name,
        applied_on=tr.applied_on,
        phi_days=tr.phi_days,
        harvest_safe_on=harvest,
        followup_due_on=tr.followup_due_on,
        area_m2=tr.area_m2,
        total_product=tr.total_product,
        estimated_cost=tr.estimated_cost,
        severity_before=tr.severity_before,
        status=tr.status,
        original_image_url=f"/api/images/{diag.original_image_path}" if diag else None,
        followups=[FollowupResponse.model_validate(f) for f in tr.followups],
        created_at=tr.created_at,
    )


def create_treatment(db: Session, user_id: int, payload: TreatmentCreate) -> Treatment:
    diag = _owned_diagnosis(db, payload.diagnosis_id, user_id)
    _usable_active(payload.active_code)
    applied_on = payload.applied_on or date.today()
    if applied_on > date.today() + timedelta(days=1):
        raise _unprocessable("Ngày phun không được ở tương lai.")
    tr = Treatment(
        user_id=user_id,
        diagnosis_id=diag.id,
        crop_code=diag.crop_code,
        disease_name=_library_disease(db, diag.crop_code, payload.disease_name) or _top_disease(diag),
        active_code=payload.active_code,
        product_name=payload.product_name,
        applied_on=applied_on,
        phi_days=payload.phi_days,
        followup_due_on=applied_on + timedelta(days=payload.followup_days),
        area_m2=payload.area_m2,
        total_product=payload.total_product,
        estimated_cost=payload.estimated_cost,
        severity_before=diag.severity_pct,
        status="awaiting_followup",
    )
    db.add(tr)
    db.commit()
    db.refresh(tr)
    return tr


def list_treatments(db: Session, user_id: int) -> list[Treatment]:
    return (
        db.query(Treatment)
        .filter(Treatment.user_id == user_id)
        .order_by(Treatment.applied_on.desc(), Treatment.id.desc())
        .all()
    )


def get_treatment(db: Session, user_id: int, treatment_id: int) -> Treatment:
    return _owned_treatment(db, treatment_id, user_id)


def delete_treatment(db: Session, user_id: int, treatment_id: int) -> None:
    db.delete(_owned_treatment(db, treatment_id, user_id))
    db.commit()


def _rotation_for(tr: Treatment) -> list[ActiveResponse]:
    used = ACTIVES_BY_CODE.get(tr.active_code)
    candidates = actives_for_disease(tr.crop_code, tr.disease_name or "")
    return [to_active_response(a, recommended=True) for a in suggest_rotation(used, candidates)]


def add_followup(db: Session, user_id: int, treatment_id: int, diagnosis_id: int) -> FollowupResult:
    tr = _owned_treatment(db, treatment_id, user_id)
    if diagnosis_id == tr.diagnosis_id:
        raise _unprocessable("Ảnh tái khám phải là một lần chụp mới, khác ảnh trước khi điều trị.")
    diag = _owned_diagnosis(db, diagnosis_id, user_id)
    if diag.crop_code != tr.crop_code:
        raise _unprocessable("Ảnh tái khám phải cùng loại cây với lần điều trị.")
    if diag.created_at < tr.created_at:
        raise _unprocessable("Ảnh tái khám phải được chụp sau khi ghi nhận lần phun thuốc.")
    if any(f.diagnosis_id == diag.id for f in tr.followups):
        raise _unprocessable("Ảnh này đã được dùng để tái khám lần điều trị này.")

    outcome = evaluate_response(tr.severity_before, diag.severity_pct)
    followup = TreatmentFollowup(
        treatment_id=tr.id,
        diagnosis_id=diag.id,
        severity_after=diag.severity_pct,
        relative_change=outcome.relative_change,
        verdict=outcome.verdict,
    )
    db.add(followup)
    tr.status = "evaluated"
    db.commit()
    db.refresh(followup)

    suggestions = _rotation_for(tr) if outcome.verdict in ("ineffective", "unclear") else []
    return FollowupResult(
        **FollowupResponse.model_validate(followup).model_dump(),
        severity_before=tr.severity_before,
        message=outcome.message,
        checklist=list(outcome.checklist),
        rotation_suggestions=suggestions,
    )


def efficacy_stats(db: Session, min_samples: int) -> list[EfficacyRow]:
    """Anonymous aggregate per active × disease, counting each treatment once (its latest
    conclusive follow-up) so one user re-photographing many times cannot skew the rate."""
    latest = (
        db.query(func.max(TreatmentFollowup.id).label("fid"))
        .filter(TreatmentFollowup.verdict != "inconclusive")
        .group_by(TreatmentFollowup.treatment_id)
        .subquery()
    )
    effective = func.sum(case((TreatmentFollowup.verdict == "effective", 1), else_=0))
    samples = func.count(func.distinct(Treatment.id))
    rows = (
        db.query(Treatment.crop_code, Treatment.disease_name, Treatment.active_code, samples, effective)
        .join(TreatmentFollowup, TreatmentFollowup.treatment_id == Treatment.id)
        .join(latest, latest.c.fid == TreatmentFollowup.id)
        .filter(Treatment.disease_name.isnot(None))
        .group_by(Treatment.crop_code, Treatment.disease_name, Treatment.active_code)
        .having(samples >= min_samples)
        .order_by(samples.desc())
        .all()
    )
    return [
        EfficacyRow(
            crop_code=crop,
            disease_name=disease,
            active_code=code,
            active_name=ACTIVES_BY_CODE.get(code, {"name": code})["name"],
            samples=n,
            effective=int(eff or 0),
            effective_rate=round((eff or 0) / n, 3),
        )
        for crop, disease, code, n, eff in rows
    ]

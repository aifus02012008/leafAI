from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.dependencies import resolve_crop
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.core.crops import get_crop
from app.models.diagnosis import DiagnosisHistory
from app.models.user import User
from app.schemas.assistant import AskRequest, AskResponse, RelatedDisease
from app.services import assistant_service

router = APIRouter(prefix="/api/assistant", tags=["Assistant"])


def _diagnosis_context(db: Session, diagnosis_id: int, user_id: int) -> assistant_service.DiagnosisContext:
    """Load the user's own diagnosis (404 for other users' ids) as chat context."""
    diag = db.query(DiagnosisHistory).filter(DiagnosisHistory.id == diagnosis_id, DiagnosisHistory.user_id == user_id).first()
    if diag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy lượt chẩn đoán.")
    top = max(diag.detections, key=lambda d: d.confidence, default=None)
    return assistant_service.DiagnosisContext(
        crop_code=diag.crop_code,
        crop_name=get_crop(diag.crop_code).name_vi,
        disease=top.class_name if top else None,
        confidence=top.confidence if top else None,
        severity_pct=diag.severity_pct,
        source="gemini" if (diag.model_version or "").startswith("gemini-vision") else "model",
    )


@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    crop_code = resolve_crop(payload.crop).code if payload.crop else None
    diagnosis = _diagnosis_context(db, payload.diagnosis_id, current_user.id) if payload.diagnosis_id else None
    if diagnosis is not None:
        crop_code = diagnosis.crop_code
    try:
        result = await run_in_threadpool(
            assistant_service.answer_question, db, current_user.id, payload.question.strip(), crop_code, diagnosis
        )
    except assistant_service.RateLimitError:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Bạn hỏi hơi nhanh, vui lòng đợi một chút rồi hỏi tiếp.",
        )
    return AskResponse(
        answer=result.answer,
        source=result.source,
        related=[RelatedDisease(id=h.id, crop_code=h.crop_code, class_name=h.class_name) for h in result.related],
    )

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.dependencies import resolve_crop
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.assistant import AskRequest, AskResponse, RelatedDisease
from app.services import assistant_service

router = APIRouter(prefix="/api/assistant", tags=["Assistant"])


@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    crop_code = resolve_crop(payload.crop).code if payload.crop else None
    try:
        result = await run_in_threadpool(
            assistant_service.answer_question, db, current_user.id, payload.question.strip(), crop_code
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

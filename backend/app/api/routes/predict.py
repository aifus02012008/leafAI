import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.api.dependencies import resolve_crop
from app.api.presenters import to_detection_responses
from app.core.crops import DEFAULT_CROP_CODE
from app.core.dependencies import get_current_user
from app.core.rate_limit import limit_predict
from app.db.session import get_db
from app.models.user import User
from app.schemas.diagnosis import PredictResponse
from app.services.gemini_skill import GeminiSkillError, GeminiSkillRateLimited
from app.services.model_registry import ModelUnavailableError
from app.services.prediction_service import (
    InconclusiveImageError,
    build_summary,
    can_diagnose,
    run_prediction,
)
from app.services.radar_service import coarsen
from app.utils.image_utils import validate_and_save_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Prediction"])


@router.post("/predict", response_model=PredictResponse)
async def predict(
    file: UploadFile = File(...),
    crop: str = Form("tea", max_length=32),
    latitude: float | None = Form(None, ge=-90, le=90),
    longitude: float | None = Form(None, ge=-180, le=180),
    share_to_radar: bool = Form(False),
    current_user: User = Depends(limit_predict),
    db: Session = Depends(get_db)
):
    crop_cfg = resolve_crop(crop)
    if not can_diagnose(crop_cfg):
        if crop_cfg.code == DEFAULT_CROP_CODE:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Dịch vụ mô hình AI tạm thời không khả dụng. Vui lòng thử lại sau."
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Mô hình chẩn đoán lá {crop_cfg.name_vi} đang được phát triển, chưa thể sử dụng."
        )

    # Location is stored only with explicit consent, and coarsened (~110 m).
    location = None
    if share_to_radar and latitude is not None and longitude is not None:
        location = (coarsen(latitude), coarsen(longitude))

    temp_path = await validate_and_save_upload(file)
    try:
        # Model loading/inference is blocking: keep it off the event loop.
        diagnosis, outcome = await run_in_threadpool(run_prediction, temp_path, current_user.id, db, crop_cfg, location)
    except InconclusiveImageError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Ảnh chưa đủ rõ để nhận diện lá {crop_cfg.name_vi.lower()}. Hãy chụp cận một chiếc lá, đủ sáng, rõ nét rồi thử lại."
        )
    except GeminiSkillRateLimited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Bạn chụp hơi nhanh. Đợi khoảng 1 phút rồi thử lại."
        )
    except GeminiSkillError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI chẩn đoán lá {crop_cfg.name_vi.lower()} đang bận. Vui lòng thử lại sau ít phút."
        )
    except ModelUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Mô hình chẩn đoán lá {crop_cfg.name_vi} tạm thời không khả dụng. Vui lòng thử lại sau."
        )
    except Exception as e:
        logger.error(f"Prediction failed for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Quá trình chẩn đoán gặp lỗi. Vui lòng thử lại."
        )
    finally:
        if Path(temp_path).exists():
            try:
                os.remove(temp_path)
            except OSError:
                pass

    detections = to_detection_responses(diagnosis)
    return PredictResponse(
        id=diagnosis.id,
        crop_code=diagnosis.crop_code,
        model_version=diagnosis.model_version,
        original_image_url=f"/api/images/{diagnosis.original_image_path}",
        result_image_url=f"/api/images/{diagnosis.result_image_path}" if diagnosis.result_image_path else None,
        status=diagnosis.status,
        inference_time=diagnosis.inference_time,
        created_at=diagnosis.created_at,
        detections=detections,
        user_feedback=diagnosis.user_feedback,
        severity_pct=diagnosis.severity_pct,
        summary=build_summary(crop_cfg, outcome, detections),
    )

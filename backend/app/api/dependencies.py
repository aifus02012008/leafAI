"""Shared request-level dependencies for API routes."""
from __future__ import annotations

from fastapi import HTTPException, Query, status

from app.core.crops import CropConfig, CropNotFoundError, get_crop


def resolve_crop(code: str) -> CropConfig:
    """Map a crop code to its config or raise HTTP 422."""
    try:
        return get_crop(code)
    except CropNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Loại cây trồng không được hỗ trợ: '{code}'.",
        )


def optional_crop_filter(crop: str | None = Query(None, max_length=32)) -> CropConfig | None:
    """Optional ``?crop=`` query parameter, validated against the crop registry."""
    if crop is None or not crop.strip():
        return None
    return resolve_crop(crop)

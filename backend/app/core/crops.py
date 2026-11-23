"""Crop registry: which crops LEAF_AI supports and how each crop's model is interpreted.

Configuration lives in ``crops.yaml`` next to this module. Every ``CropConfig`` is
immutable; lookups go through :func:`get_crop` / :func:`list_crops`.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import yaml

from app.core.config import LABEL_MAPPING, settings

CROPS_FILE = Path(__file__).with_name("crops.yaml")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CROP_CODE = "tea"
SETTINGS_WEIGHTS = "settings"


class CropNotFoundError(LookupError):
    """Raised when a crop code is not configured."""

    def __init__(self, code: str):
        super().__init__(f"Unsupported crop: {code!r}")
        self.code = code


@dataclass(frozen=True)
class CropConfig:
    code: str
    name_vi: str
    name_en: str
    scientific_name: str
    weights_path: str | None
    model_version: str | None
    img_size: int
    base_confidence: float
    default_threshold: float
    healthy_threshold: float
    label_map: Mapping[str, str]
    thresholds: Mapping[str, float]
    healthy_labels: frozenset[str]

    def map_label(self, raw_label: str | None) -> str:
        """Translate a raw model label into the canonical disease name for this crop."""
        clean = (raw_label or "").strip()
        return self.label_map.get(clean, clean)

    def is_healthy_label(self, raw_label: str) -> bool:
        return raw_label.strip().lower() in self.healthy_labels

    def threshold_for(self, raw_label: str) -> float:
        clean = raw_label.strip()
        if clean in self.thresholds:
            return self.thresholds[clean]
        return self.thresholds.get(self.map_label(clean), self.default_threshold)

    @property
    def weights_exist(self) -> bool:
        return bool(self.weights_path) and Path(self.weights_path).is_file()


def _resolve_weights(code: str, raw: str | None) -> str | None:
    if raw == SETTINGS_WEIGHTS:
        return settings.resolved_model_path
    override = os.environ.get(f"MODEL_PATH_{code.upper()}")
    candidate = override or raw
    if not candidate:
        return None
    path = Path(candidate)
    return str(path if path.is_absolute() else (PROJECT_ROOT / path).resolve())


def _build_tea(entry: Mapping[str, Any]) -> CropConfig:
    thresholds = dict(settings.CLASS_CONFIDENCE_THRESHOLDS)
    return CropConfig(
        code=entry["code"],
        name_vi=entry["name_vi"],
        name_en=entry["name_en"],
        scientific_name=entry["scientific_name"],
        weights_path=_resolve_weights(entry["code"], SETTINGS_WEIGHTS),
        model_version=entry.get("model_version"),
        img_size=settings.MODEL_IMG_SIZE,
        base_confidence=settings.MODEL_CONFIDENCE_THRESHOLD,
        default_threshold=settings.DEFAULT_CLASS_CONFIDENCE,
        healthy_threshold=thresholds.get("Healthy", 0.35),
        label_map=MappingProxyType(dict(LABEL_MAPPING)),
        thresholds=MappingProxyType(thresholds),
        healthy_labels=frozenset({"healthy"}),
    )


def _build_crop(entry: Mapping[str, Any]) -> CropConfig:
    if entry.get("weights") == SETTINGS_WEIGHTS:
        return _build_tea(entry)
    healthy = entry.get("healthy_labels") or ["Healthy"]
    return CropConfig(
        code=entry["code"],
        name_vi=entry["name_vi"],
        name_en=entry["name_en"],
        scientific_name=entry["scientific_name"],
        weights_path=_resolve_weights(entry["code"], entry.get("weights")),
        model_version=entry.get("model_version"),
        img_size=int(entry.get("img_size", settings.MODEL_IMG_SIZE)),
        base_confidence=float(entry.get("base_confidence", settings.MODEL_CONFIDENCE_THRESHOLD)),
        default_threshold=float(entry.get("default_threshold", settings.DEFAULT_CLASS_CONFIDENCE)),
        healthy_threshold=float(entry.get("healthy_threshold", 0.35)),
        label_map=MappingProxyType(dict(entry.get("label_map") or {})),
        thresholds=MappingProxyType({k: float(v) for k, v in (entry.get("thresholds") or {}).items()}),
        healthy_labels=frozenset(label.strip().lower() for label in healthy),
    )


@lru_cache(maxsize=1)
def list_crops() -> tuple[CropConfig, ...]:
    """All configured crops, in display order (tea first)."""
    try:
        raw = yaml.safe_load(CROPS_FILE.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"Cannot read crop configuration {CROPS_FILE}: {exc}") from exc
    entries = raw.get("crops") or []
    if not entries:
        raise RuntimeError(f"No crops configured in {CROPS_FILE}")
    return tuple(_build_crop(entry) for entry in entries)


def get_crop(code: str | None) -> CropConfig:
    """Look up a crop by code (case-insensitive). Raises CropNotFoundError."""
    wanted = (code or "").strip().lower()
    for crop in list_crops():
        if crop.code == wanted:
            return crop
    raise CropNotFoundError(code or "")

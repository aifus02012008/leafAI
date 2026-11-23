"""Per-crop model registry with lazy loading and a small LRU cache.

Each crop has its own detection model (see app/core/crops.yaml). Models are loaded
on first use; at most ``settings.MAX_LOADED_MODELS`` stay in memory so the server
fits in small instances. Tests (and future non-YOLO backends) can inject a
detector with :meth:`ModelRegistry.register`.
"""
from __future__ import annotations

import logging
import threading
from collections import OrderedDict
from typing import Protocol

from app.core.config import settings
from app.core.crops import CropConfig
from app.services.detection_rules import RawDetection

logger = logging.getLogger(__name__)


class ModelUnavailableError(RuntimeError):
    """The crop has no model weights or the model failed to load."""


class Detector(Protocol):
    version: str | None
    class_names: dict[int, str]
    kind: str  # "detect" (lesion boxes) or "classify" (whole-leaf label)

    def detect(self, image_path: str) -> list[RawDetection]: ...


# A classifier returns one score per class; keep only the few plausible ones.
MAX_CLASSIFY_CANDIDATES = 3


class YoloDetector:
    """Ultralytics YOLO wrapper (detect or classify) that returns framework-free RawDetection objects.

    Classification models (trained from folder-per-class datasets) have no lesion boxes, so each
    candidate class is reported with a box covering the whole image.
    """

    def __init__(self, crop: CropConfig):
        from ultralytics import YOLO  # heavy import, only when a model is actually needed

        self._crop = crop
        self._model = YOLO(crop.weights_path)
        self._infer_lock = threading.Lock()  # Ultralytics predict is not thread-safe
        self.version = crop.model_version
        names = getattr(self._model, "names", None) or {}
        self.class_names = {int(k): str(v) for k, v in dict(names).items()}
        self.kind = "classify" if getattr(self._model, "task", "detect") == "classify" else "detect"

    def detect(self, image_path: str) -> list[RawDetection]:
        with self._infer_lock:
            results = self._model.predict(
                source=image_path,
                conf=self._crop.base_confidence,
                imgsz=self._crop.img_size,
                verbose=False,
            )
        if not results:
            return []
        if self.kind == "classify":
            return self._classify_candidates(results[0])
        if results[0].boxes is None:
            return []
        boxes = results[0].boxes
        detections = []
        for idx in range(len(boxes)):
            box = boxes[idx]
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().tolist()
            cls_idx = int(box.cls[0].cpu().numpy())
            detections.append(RawDetection(
                label=self.class_names.get(cls_idx, f"Class_{cls_idx}"),
                confidence=float(box.conf[0].cpu().numpy()),
                x1=x1, y1=y1, x2=x2, y2=y2,
            ))
        return detections

    def _classify_candidates(self, result) -> list[RawDetection]:
        probs = getattr(result, "probs", None)
        if probs is None:
            return []
        height, width = result.orig_shape[:2]
        scores = probs.data.cpu().numpy().tolist()
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:MAX_CLASSIFY_CANDIDATES]
        return [
            RawDetection(
                label=self.class_names.get(i, f"Class_{i}"),
                confidence=float(scores[i]),
                x1=0.0, y1=0.0, x2=float(width), y2=float(height),
            )
            for i in ranked
            if scores[i] >= self._crop.base_confidence
        ]


class ModelRegistry:
    def __init__(self, max_loaded: int):
        self._max_loaded = max(1, max_loaded)
        self._loaded: OrderedDict[str, Detector] = OrderedDict()
        self._overrides: dict[str, Detector] = {}
        self._errors: dict[str, str] = {}
        self._lock = threading.Lock()

    # ----- injection (tests / alternative backends) -----
    def register(self, crop_code: str, detector: Detector) -> None:
        self._overrides[crop_code] = detector

    def unregister(self, crop_code: str) -> None:
        self._overrides.pop(crop_code, None)

    # ----- status -----
    def is_available(self, crop: CropConfig) -> bool:
        return crop.code in self._overrides or crop.weights_exist

    def is_loaded(self, crop_code: str) -> bool:
        return crop_code in self._overrides or crop_code in self._loaded

    def load_error(self, crop_code: str) -> str | None:
        return self._errors.get(crop_code)

    def class_names(self, crop_code: str) -> dict[int, str]:
        detector = self._overrides.get(crop_code) or self._loaded.get(crop_code)
        return dict(detector.class_names) if detector else {}

    # ----- access -----
    def get(self, crop: CropConfig) -> Detector:
        """Return the crop's detector, loading it if needed. Raises ModelUnavailableError."""
        if crop.code in self._overrides:
            return self._overrides[crop.code]
        if not crop.weights_exist:
            raise ModelUnavailableError(f"No model weights for crop '{crop.code}'")
        with self._lock:
            if crop.code in self._loaded:
                self._loaded.move_to_end(crop.code)
                return self._loaded[crop.code]
            detector = self._load(crop)
            self._loaded[crop.code] = detector
            self._evict_if_needed()
            return detector

    def _load(self, crop: CropConfig) -> Detector:
        logger.info("Loading model for crop '%s' from %s", crop.code, crop.weights_path)
        try:
            detector = YoloDetector(crop)
        except Exception as exc:  # ultralytics raises a variety of errors
            self._errors[crop.code] = str(exc)
            logger.error("Failed to load model for crop '%s': %s", crop.code, exc, exc_info=True)
            raise ModelUnavailableError(f"Model for crop '{crop.code}' failed to load") from exc
        self._errors.pop(crop.code, None)
        logger.info("Model for '%s' ready. Classes: %s", crop.code, detector.class_names)
        return detector

    def _evict_if_needed(self) -> None:
        while len(self._loaded) > self._max_loaded:
            evicted, _ = self._loaded.popitem(last=False)
            logger.info("Evicted model for crop '%s' (LRU, max=%d)", evicted, self._max_loaded)


model_registry = ModelRegistry(max_loaded=settings.MAX_LOADED_MODELS)

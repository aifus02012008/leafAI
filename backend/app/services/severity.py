"""Lesion severity: percentage of leaf area covered by lesions.

Classical computer vision (no training needed):
1. Green tissue  = Excess-Green index (2G - R - B) above a threshold.
2. Lesion colour = brown/yellow hues or very dark necrotic pixels.
3. Leaf mask     = external contours of (green ∪ lesion) that are mostly green
                   (rejects brown soil / background) with holes filled.
4. Severity      = lesion-coloured pixels inside the leaf mask / leaf mask pixels
                   (glare, background gaps and pale tissue are not counted as lesion).

Using a ratio (not absolute pixels) makes before/after photos comparable even when
the camera distance differs. Returns None when no leaf can be found.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import cv2
import numpy as np

logger = logging.getLogger(__name__)

MAX_SIDE = 1024
EXG_GREEN_MIN = 20
MIN_LEAF_FRACTION = 0.01          # leaf must cover >= 1% of the image
MIN_GREEN_SHARE_IN_LEAF = 0.25    # a "leaf" component must be at least 25% green


@dataclass(frozen=True)
class SeverityResult:
    severity_pct: float
    leaf_pixels: int
    lesion_pixels: int


def _read(path: str) -> np.ndarray | None:
    data = np.fromfile(path, dtype=np.uint8)  # handles non-ASCII Windows paths
    img = cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None
    if img is None:
        return None
    h, w = img.shape[:2]
    scale = MAX_SIDE / max(h, w)
    if scale < 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def _masks(img: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    b, g, r = [c.astype(np.int16) for c in cv2.split(img)]
    green = (2 * g - r - b) > EXG_GREEN_MIN
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hue, sat, val = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    brownish = (hue <= 35) & (sat > 60) & (val > 30)
    necrotic = (val < 60) & (sat > 30)
    return green, (brownish | necrotic) & ~green


def _leaf_mask(green: np.ndarray, lesion: np.ndarray) -> np.ndarray:
    plant = ((green | lesion).astype(np.uint8)) * 255
    plant = cv2.morphologyEx(plant, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    contours, _ = cv2.findContours(plant, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    leaf = np.zeros_like(plant)
    min_area = MIN_LEAF_FRACTION * plant.size
    for cnt in contours:
        if cv2.contourArea(cnt) < min_area:
            continue
        candidate = np.zeros_like(plant)
        cv2.drawContours(candidate, [cnt], -1, 255, thickness=cv2.FILLED)
        inside = candidate > 0
        if green[inside].mean() >= MIN_GREEN_SHARE_IN_LEAF:
            leaf |= candidate
    return leaf > 0


def measure_severity(image_path: str) -> SeverityResult | None:
    try:
        img = _read(image_path)
        if img is None:
            return None
        green, _lesion_colour = _masks(img)
        leaf = _leaf_mask(green, _lesion_colour)
        leaf_px = int(leaf.sum())
        if leaf_px < MIN_LEAF_FRACTION * leaf.size:
            return None
        lesion_px = int((leaf & _lesion_colour).sum())
        return SeverityResult(
            severity_pct=round(lesion_px / leaf_px * 100, 2),
            leaf_pixels=leaf_px,
            lesion_pixels=lesion_px,
        )
    except (cv2.error, ValueError, OSError) as exc:
        logger.warning("Severity measurement failed for %s: %s", image_path, exc)
        return None

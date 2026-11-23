import time
import uuid
import shutil
import logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from sqlalchemy.orm import Session
from app.models.diagnosis import DiagnosisHistory
from app.models.detection import DetectionResult
from app.core.config import settings
from app.core.crops import CropConfig
from app.services.detection_rules import DetectionOutcome, evaluate_detections
from app.services.model_registry import model_registry
from app.services.severity import measure_severity
from app.services.storage import StorageError, get_storage

logger = logging.getLogger(__name__)

# Distinct colors matching the reference UI palette (teal, purple, amber, cyan, pink, lime)
BOX_PALETTE = [
    {"stroke": (34, 211, 238), "bg": (34, 211, 238, 220), "text": (10, 15, 10)},    # Cyan
    {"stroke": (192, 132, 252), "bg": (192, 132, 252, 220), "text": (10, 15, 10)}, # Purple
    {"stroke": (52, 211, 153), "bg": (52, 211, 153, 220), "text": (10, 15, 10)},   # Emerald
    {"stroke": (251, 191, 36), "bg": (251, 191, 36, 220), "text": (10, 15, 10)},   # Amber
    {"stroke": (248, 113, 113), "bg": (248, 113, 113, 220), "text": (10, 15, 10)}, # Coral Red
    {"stroke": (244, 114, 182), "bg": (244, 114, 182, 220), "text": (10, 15, 10)}, # Pink
]

def clean_class_display(name: str) -> str:
    """Format an already-mapped disease label for drawing on the image."""
    return name.replace("Tomato___", "").replace("_", " ")

def draw_bounding_boxes(image_path: str, detections: list[dict], output_path: str) -> str:
    """Draw clear, modern bounding boxes with stylized tags matching reference UI."""
    img = Image.open(image_path).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Try system fonts, fall back gracefully
    font = None
    for font_path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
    ]:
        if Path(font_path).exists():
            try:
                font = ImageFont.truetype(font_path, 16)
                break
            except Exception:
                pass
    if font is None:
        font = ImageFont.load_default()
        
    width, height = img.size
    
    for i, det in enumerate(detections):
        palette = BOX_PALETTE[i % len(BOX_PALETTE)]
        stroke_color = palette["stroke"]
        
        # Clamp coordinates
        x1 = max(0, min(float(det["x1"]), width - 1))
        y1 = max(0, min(float(det["y1"]), height - 1))
        x2 = max(0, min(float(det["x2"]), width - 1))
        y2 = max(0, min(float(det["y2"]), height - 1))
        
        # Draw bounding rectangle with 3px border
        for offset in range(3):
            draw.rectangle(
                [x1 - offset, y1 - offset, x2 + offset, y2 + offset],
                outline=(*stroke_color, 255)
            )
            
        # Draw translucent corner accents
        corner_len = min(20, (x2 - x1) / 3, (y2 - y1) / 3)
        if corner_len > 5:
            # Top-left, top-right, bottom-left, bottom-right accents
            accent_color = (255, 255, 255, 200)
            draw.line([(x1, y1), (x1 + corner_len, y1)], fill=accent_color, width=4)
            draw.line([(x1, y1), (x1, y1 + corner_len)], fill=accent_color, width=4)
            draw.line([(x2, y1), (x2 - corner_len, y1)], fill=accent_color, width=4)
            draw.line([(x2, y1), (x2, y1 + corner_len)], fill=accent_color, width=4)
            
        # Label text: e.g. "#1 | Bacterial Spot (88%)"
        cls_clean = clean_class_display(det["class_name"])
        conf_pct = det["confidence"] * 100
        label_text = f"#{i+1} | {cls_clean} ({conf_pct:.0f}%)"
        
        bbox = draw.textbbox((0, 0), label_text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        
        # Place label above box if space permits, otherwise inside
        label_y1 = y1 - text_h - 10
        if label_y1 < 0:
            label_y1 = y1 + 4
        label_y2 = label_y1 + text_h + 8
        label_x1 = max(0, x1)
        label_x2 = min(width, label_x1 + text_w + 16)
        
        # Draw label background badge (rounded rect)
        draw.rounded_rectangle(
            [label_x1, label_y1, label_x2, label_y2],
            radius=4,
            fill=palette["bg"]
        )
        draw.text(
            (label_x1 + 8, label_y1 + 4),
            label_text,
            fill=palette["text"],
            font=font
        )
        
    # Composite overlay
    composed = Image.alpha_composite(img, overlay).convert("RGB")
    composed.save(output_path, "JPEG", quality=92)
    return output_path

def _store_original(image_path: str) -> tuple[str, Path]:
    """Copy the validated upload into permanent storage; returns (uid, destination)."""
    uid = uuid.uuid4().hex[:12]
    ext = Path(image_path).suffix.lower() or ".jpg"
    dest = settings.originals_dir / f"{uid}_orig{ext}"
    shutil.copy2(image_path, str(dest))
    _strip_metadata(dest)
    return uid, dest


def _strip_metadata(path: Path) -> None:
    """Remove EXIF (GPS position, device info) from a stored photo; keep its visual orientation."""
    try:
        with Image.open(path) as img:
            fmt = img.format or "JPEG"
            clean = ImageOps.exif_transpose(img)
            clean.info.pop("exif", None)
            options = {"quality": 95} if fmt in ("JPEG", "WEBP") else {}
            if fmt == "JPEG" and clean.mode not in ("RGB", "L"):
                clean = clean.convert("RGB")
            clean.save(path, format=fmt, **options)
    except (OSError, ValueError) as exc:
        logger.warning("Could not strip metadata from %s: %s", path.name, exc)


def _render_annotated(uid: str, orig_dest: Path, detections: tuple[dict, ...]) -> str | None:
    if not detections:
        return None
    result_filename = f"{uid}_annotated.jpg"
    draw_bounding_boxes(str(orig_dest), list(detections), str(settings.results_dir / result_filename))
    return f"results/{result_filename}"


def _persist(
    db: Session,
    *,
    user_id: int,
    crop: CropConfig,
    model_version: str | None,
    orig_rel_path: str,
    result_rel_path: str | None,
    outcome: DetectionOutcome,
    inference_time: float,
    severity_pct: float | None = None,
    location: tuple[float, float] | None = None,
) -> DiagnosisHistory:
    diagnosis = DiagnosisHistory(
        user_id=user_id,
        crop_code=crop.code,
        model_version=model_version,
        original_image_path=orig_rel_path,
        result_image_path=result_rel_path,
        status=outcome.status,
        inference_time=round(inference_time, 3),
        severity_pct=severity_pct,
        latitude=location[0] if location else None,
        longitude=location[1] if location else None,
        share_to_radar=location is not None,
    )
    db.add(diagnosis)
    db.flush()
    for det in outcome.detections:
        db.add(DetectionResult(history_id=diagnosis.id, **det))
    db.commit()
    db.refresh(diagnosis)
    return diagnosis


def run_prediction(
    image_path: str,
    user_id: int,
    db: Session,
    crop: CropConfig,
    location: tuple[float, float] | None = None,
) -> tuple[DiagnosisHistory, DetectionOutcome]:
    """Run the crop's model on an uploaded image, persist the diagnosis and return it with its outcome.

    Raises ModelUnavailableError when the crop has no usable model.
    """
    detector = model_registry.get(crop)
    start_time = time.time()
    uid, orig_dest = _store_original(image_path)
    result_rel_path: str | None = None
    try:
        outcome = evaluate_detections(detector.detect(str(orig_dest)), crop)
        inference_time = time.time() - start_time
        if outcome.unclear_disease_suppressed:
            logger.info("Suppressed unclear disease in favor of Healthy (%s)", outcome.healthy_confidence)
        result_rel_path = _render_annotated(uid, orig_dest, outcome.detections)
        severity = measure_severity(str(orig_dest))
        diagnosis = _persist(
            db,
            user_id=user_id,
            crop=crop,
            model_version=getattr(detector, "version", None),
            orig_rel_path=f"originals/{orig_dest.name}",
            result_rel_path=result_rel_path,
            outcome=outcome,
            inference_time=inference_time,
            severity_pct=severity.severity_pct if severity else None,
            location=location,
        )
    except Exception:
        db.rollback()
        _remove_quietly(orig_dest)
        if result_rel_path:
            _remove_quietly(settings.storage_dir / result_rel_path)
        raise
    _upload(f"originals/{orig_dest.name}", orig_dest)
    if result_rel_path:
        _upload(result_rel_path, settings.storage_dir / result_rel_path)
    return diagnosis, outcome


def _upload(key: str, path: Path) -> None:
    """Best-effort copy to the remote store (no-op for local storage).

    A remote outage must not fail the diagnosis: the local copy is still served.
    """
    try:
        get_storage().save(key, path)
    except StorageError as exc:
        logger.warning("Remote image upload failed for %s (%s)", key, type(exc).__name__)


def _remove_quietly(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        logger.warning("Could not remove orphaned file %s", path)


def build_summary(crop: CropConfig, outcome: DetectionOutcome, detections: list) -> str:
    """Human-readable Vietnamese summary of a diagnosis."""
    leaf = f"lá {crop.name_vi.lower()}"
    if not detections:
        conf = outcome.healthy_confidence
        if conf:
            if outcome.unclear_disease_suppressed:
                return (
                    f"Mô hình xác nhận {leaf} khỏe mạnh với độ tin cậy {conf * 100:.1f}%. "
                    "Các triệu chứng nghi ngờ mờ nhạt hoặc không đủ rõ ràng để xác nhận bệnh hại."
                )
            return (
                f"Mô hình xác nhận {leaf} khỏe mạnh (Healthy) với độ tin cậy {conf * 100:.1f}%. "
                "Không phát hiện dấu hiệu bệnh hại."
            )
        return f"Không phát hiện dấu hiệu bệnh hại trên lá ở ngưỡng độ tin cậy hiện tại. {leaf.capitalize()} khỏe mạnh."
    top = max(detections, key=lambda d: d.confidence)
    name = top.class_name.replace("Tomato___", "").replace("_", " ")
    return (
        f"Phát hiện dấu hiệu {name} trên {leaf} với độ tin cậy {top.confidence * 100:.1f}% "
        f"trên {len(detections)} vùng tổn thương."
    )

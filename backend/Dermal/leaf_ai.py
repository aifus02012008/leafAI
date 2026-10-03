# -*- coding: utf-8 -*-
"""
LEAF_AI — Pipeline chẩn đoán bệnh cây trồng bằng Gemini Vision.

Thay thế AI server (YOLOv8) khi model chưa kịp bàn giao. Luồng xử lý:

    1. Ảnh upload được lưu vào DB (Leaf_image) -> lấy LINK ẢNH từ DB
       (record.image.url — URL tuyệt đối kiểu Cloudinary hoặc URL tương đối /media/...)
    2. Đọc link đó ra bytes (download nếu là URL http/https, đọc storage nếu tương đối)
       —_bytes sau đó được SDK google-genai mã hoá base64 (inline_data) khi gửi lên API
    3. Gửi Gemini API (multimodal: ảnh + prompt) -> JSON
       {healthy, diseases[], regions[], report_html}
    4. Chuẩn hoá dữ liệu bệnh theo knowledge base 6 bệnh cà chua + sanitize HTML báo cáo
       -> FE render (SPA /app/... và template result.html).

Module này KHÔNG phụ vụ ngoài Gemini: mọi truy vấn HTTP đều có timeout,
không bao giờ để exception thoát ra ngoài — caller nhận dict analysis
kèm cờ analysis_unavailable khi dịch vụ lỗi.
"""

import base64
import io
import json
import logging
import mimetypes
import os
import re

import bleach
import requests
from django.core.cache import cache
from google import genai
from google.genai import types
from PIL import Image

from .leaf_knowledge import TOMATO_DISEASES

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------------------
# Model versions (giữ nguyên contract cũ: "v3" production / "v4" experimental)
# --------------------------------------------------------------------------------------
MODEL_V3 = "v3"  # production: 3 bệnh (Bacterial_spot, Early_blight, Late_blight)
MODEL_V4 = "v4"  # experimental: 6 bệnh (toàn bộ TOMATO_DISEASES)
VALID_MODELS = (MODEL_V3, MODEL_V4)

V3_CLASSES = ("Bacterial_spot", "Early_blight", "Late_blight")
V4_CLASSES = tuple(TOMATO_DISEASES.keys())
DISEASE_CLASSES = V4_CLASSES

# --------------------------------------------------------------------------------------
# Giới hạn
# --------------------------------------------------------------------------------------
MAX_IMAGE_BYTES = 10 * 1024 * 1024   # đồng bộ limit upload 10MB
IMAGE_FETCH_TIMEOUT = 20             # giây — tải ảnh qua link (Cloudinary)
GEMINI_TIMEOUT_MS = 45_000           # ms — dưới timeout 60s của FE api.js
GEMINI_MAX_OUTPUT_TOKENS = 8192      # chặn phình chi phí / JSON bị cắt giữa chừng
MAX_REPORT_CHARS = 40_000            # trần ký tự báo cáo hiển thị

# Gemini chấp nhận các định dạng này trực tiếp; khác sẽ thử convert sang JPEG bằng Pillow
SUPPORTED_IMAGE_MIMES = {
    "image/jpeg", "image/png", "image/webp", "image/gif", "image/heic", "image/heif",
}


class DiagnosisUnavailable(Exception):
    """Không phân tích được ảnh. `str(e)` là thông báo tiếng Việt sẵn cho người dùng."""


# --------------------------------------------------------------------------------------
# Rate-limit (cache-based, dùng chung cho upload legacy và /api/diagnose/)
# --------------------------------------------------------------------------------------
def throttled(key, limit, seconds):
    """Đếm đơn giản bằng cache. Trả về True nếu vượt limit."""
    try:
        hits = cache.get(key, 0)
        if hits >= limit:
            return True
        cache.set(key, hits + 1, seconds)
    except Exception:
        logger.warning("cache throttle unavailable")
    return False


# --------------------------------------------------------------------------------------
# HTML report: whitelist tag/attr để render an toàn (|safe / innerHTML)
# --------------------------------------------------------------------------------------
REPORT_TAGS = [
    "h3", "h4", "p", "ul", "ol", "li", "strong", "em", "b", "i", "small",
    "br", "hr", "div", "span", "table", "thead", "tbody", "tr", "th", "td", "a",
]
REPORT_ATTRS = {
    "*": ["class"],
    "a": ["href", "title", "rel"],
    "th": ["colspan", "rowspan"],
    "td": ["colspan", "rowspan"],
}

# Bộ class mà prompt yêu cầu Gemini dùng (FE chỉ style đúng bộ này)
REPORT_CLASSES = (
    "badge", "badge-high", "badge-mid", "badge-low",
    "pct", "report-table", "callout", "callout-warn", "callout-info",
)


def _prune_unknown_classes(html):
    """Giữ lại chỉ các class thuộc REPORT_CLASSES — FE chỉ style đúng bộ này."""

    def _keep(match):
        kept = [c for c in match.group(1).split() if c in REPORT_CLASSES]
        return 'class="{}"'.format(" ".join(kept)) if kept else ""

    return re.sub(r'class="([^"]*)"', _keep, html)


def sanitize_report_html(html):
    """Làm sạch HTML báo cáo từ Gemini (whitelist tag/attr, chặn script/style/on*)."""
    if not html or not str(html).strip():
        return ""
    try:
        clean = bleach.clean(
            str(html),
            tags=REPORT_TAGS,
            attributes=REPORT_ATTRS,
            protocols=("http", "https", "mailto"),
            strip=True,
        )
        clean = _prune_unknown_classes(clean.strip())
        return clean[:MAX_REPORT_CHARS]
    except Exception:
        logger.exception("sanitize_report_html thất bại")
        return ""


# --------------------------------------------------------------------------------------
# Prompt
# --------------------------------------------------------------------------------------
def _active_disease_lines(model_version):
    codes = V3_CLASSES if model_version == MODEL_V3 else V4_CLASSES
    return "\n".join(
        "- {} — {}".format(code, TOMATO_DISEASES[code]["name_vi"]) for code in codes
    )


def build_diagnosis_prompt(context_text="", model_version=MODEL_V3):
    """Prompt tiếng Việt, ép Gemini trả JSON {healthy, diseases, regions, report_html}."""
    if model_version not in VALID_MODELS:
        model_version = MODEL_V3

    ctx = (context_text or "").strip()
    ctx_block = ""
    if ctx:
        ctx_block = (
            "\nTHÔNG TIN BỔ SUNG TỪ NGƯỜI DÙNG "
            "(hãy lồng ghép tự nhiên vào phần phân tích):\n" + ctx + "\n"
        )

    return f"""Bạn là chuyên gia bệnh học cây cà chua (plant pathologist) của LEAF_AI.
Nhiệm vụ: phân tích ẢNH LÁ đính kèm và trả về đúng MỘT JSON object thuần (UTF-8),
không markdown, không lời dẫn, không giải thích ngoài JSON.

Các bệnh được phép chẩn đoán (chỉ dùng đúng mã này cho trường "class"):
{_active_disease_lines(model_version)}
Nếu lá không thấy dấu hiệu bệnh nào, đặt "healthy": true và để diseases/regions rỗng.

CẤU TRÚC JSON:
{{
  "healthy": false,
  "diseases": [{{"class": "Early_blight", "probability": 87}}],
  "regions": [{{"class": "Early_blight", "confidence": 0.87, "bbox": [512, 96, 224, 192]}}],
  "report_html": "<h3>Kết luận nhanh</h3><p>...</p>"
}}

QUY TẮC BẮT BUỘC:
1. "diseases": tối đa 3 mục, sắp theo "probability" GIẢM DẦN; "probability" là số 0-100
   (không kèm dấu %, không chuỗi chữ). Không trùng mã bệnh. healthy=true thì diseases=[].
2. "regions": tối đa 4 vùng khoanh rõ nhất trên ảnh; "bbox" = [x, y, w, h] toạ độ TUYỆT ĐỐI
   theo thang 0-1000 (góc trên-trái ảnh = 0,0; x sang phải, y xuống dưới).
   Không chắc chắn vị trí thì để regions=[].
3. "report_html": tiếng Việt, HTML semantic thuần. CẤM TUYỆT: <style>, <script>, <img>,
   <iframe>, thuộc tính style/on*, markdown (#, **). Chỉ dùng thẻ:
   h3, h4, p, ul, ol, li, strong, em, b, i, br, hr, div, span, table, thead, tbody,
   tr, th, td, a, small.
   Chỉ dùng các class: badge, badge-high, badge-mid, badge-low, pct, report-table,
   callout, callout-warn, callout-info.
4. report_html đúng 6 phần, mỗi phần mở đầu bằng <h3>:
   a) <h3>Kết luận nhanh</h3> — 1-2 câu chốt bệnh chính + số % và
      <span class="badge badge-high|badge-mid|badge-low">Mức độ</span>
      (badge-high = Nghiêm trọng, badge-mid = Trung bình, badge-low = Nhẹ).
   b) <h3>Quan sát trên ảnh</h3> — mô tả cụ thể những gì THẤY được trên ảnh:
      hình dạng, màu, kích thước ước lượng, vị trí (mặt trên/mặt dưới lá, mép/giữa,
      lá già/lá non). Không bịa thêm triệu chứng không nhìn thấy.
   c) <h3>Bệnh chính và mức độ</h3> — nêu tên bệnh kèm <span class="pct">87%</span>;
      nếu nhiều bệnh, dùng <table class="report-table"> với cột: Bệnh | Độ tin cậy | Mức độ.
   d) <h3>Nguyên nhân và điều kiện thuận lợi</h3> — thời tiết/ẩm độ thường khiến bệnh bùng.
   e) <h3>Phác đồ xử lý</h3> — 3 nhóm gạch đầu dòng: Canh tác / Sinh học / Hóa học;
      nhóm hóa học nhắc nguyên tắc 4 đúng (đúng thuốc, đúng lúc, đúng nồng độ, đúng cách).
   f) <h3>Phòng ngừa và lưu ý</h3> — kết thúc đúng câu:
      "AI chỉ hỗ trợ chẩn đoán sơ bộ — hãy tham khảo chuyên gia nông nghiệp hoặc
      trung tâm bảo vệ thực vụ trước khi phun thuốc."
5. Mức độ theo "probability": >=60 → "Nghiêm trọng"; 35-59 → "Trung bình"; <35 → "Nhẹ".
   Mọi phần trăm trong report_html phải KHỚP với "diseases".
6. healthy=true: report_html nêu lá khỏe mạnh + dặn thăm vườn 2 lần/tuần.
{ctx_block}
Trả về JSON ngay, không kèm ký tự nào ngoài JSON."""


# --------------------------------------------------------------------------------------
# Đọc ảnh từ DB (link -> bytes)
# --------------------------------------------------------------------------------------
def _fetch_url_bytes(url):
    """Tải ảnh qua URL tuyệt đối (Cloudinary...). Trả về bytes hoặc None nếu lỗi."""
    resp = None
    try:
        resp = requests.get(url, timeout=IMAGE_FETCH_TIMEOUT, stream=True)
        resp.raise_for_status()
        chunks = []
        total = 0
        for chunk in resp.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            chunks.append(chunk)
            total += len(chunk)
            if total > MAX_IMAGE_BYTES:
                logger.warning("Ảnh qua link vượt quá %d bytes: %s", MAX_IMAGE_BYTES, url)
                return None
        return b"".join(chunks)
    except Exception as e:
        logger.warning("Không tải được ảnh qua link %s: %s", url, e)
        return None
    finally:
        if resp is not None:
            try:
                resp.close()
            except Exception:
                pass


def load_image_via_db_link(record, fallback_bytes=None):
    """
    Lấy link ảnh TỪ DB (record.image.url) rồi đọc ra bytes.

    - URL http/https (Cloudinary) → download qua requests (timeout 20s)
    - URL tương đối /media/... (FileSystemStorage) → đọc trực tiếp từ storage
    - Mọi đường lỗi → dùng `fallback_bytes` (bytes vừa upload) nếu có
    Trả về (bytes, url). Ném DiagnosisUnavailable nếu không đọc được gì.
    """
    url = ""
    if record is not None:
        try:
            url = record.image.url or ""
        except Exception:
            url = ""

    data = None
    if url.startswith(("http://", "https://")):
        data = _fetch_url_bytes(url)

    if data is None and record is not None:
        try:
            with record.image.open("rb") as fh:
                data = fh.read()
        except Exception as e:
            logger.warning("Không đọc được ảnh từ storage (record=%s): %s",
                           getattr(record, "id", None), e)

    if not data:
        data = fallback_bytes

    if not data:
        raise DiagnosisUnavailable("Không đọc được ảnh từ cơ sở dữ liệu. Hãy tải lại ảnh.")
    if len(data) > MAX_IMAGE_BYTES:
        raise DiagnosisUnavailable("Ảnh vượt quá giới hạn 10MB.")
    return data, url


_MIME_BY_PIL_FORMAT = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
    "GIF": "image/gif",
    "HEIC": "image/heic",
    "HEIF": "image/heif",
    "BMP": "image/bmp",
    "TIFF": "image/tiff",
}


def _ensure_supported_image(data, url=""):
    """Trả về (bytes, mime) hợp lệ với Gemini; convert sang JPEG nếu định dạng lạ."""
    mime = ""
    try:
        fmt = Image.open(io.BytesIO(data)).format
        if fmt:
            mime = _MIME_BY_PIL_FORMAT.get(fmt, "").lower()
    except Exception:
        mime = ""

    if mime in SUPPORTED_IMAGE_MIMES:
        return data, mime

    # Thử chuyển sang JPEG (bmp, tiff, webp lạ mã hoá sai...)
    try:
        im = Image.open(io.BytesIO(data)).convert("RGB")
        buf = io.BytesIO()
        im.save(buf, format="JPEG", quality=90)
        logger.info("Đã convert ảnh không hỗ trợ (%s) sang JPEG", mime or "không rõ")
        return buf.getvalue(), "image/jpeg"
    except Exception as e:
        logger.warning("Không convert được ảnh sang JPEG: %s", e)

    guessed, _ = mimetypes.guess_type(url or "")
    if guessed in SUPPORTED_IMAGE_MIMES:
        return data, guessed
    raise DiagnosisUnavailable("Định dạng ảnh không được hỗ trợ (chấp nhận JPEG/PNG/WEBP/GIF).")


def image_size(data, default=(640, 640)):
    """Kích thước (w, h) của ảnh; fallback (640, 640) nếu không đọc được."""
    try:
        with Image.open(io.BytesIO(data)) as im:
            return im.size
    except Exception:
        return default


# --------------------------------------------------------------------------------------
# Gọi Gemini
# --------------------------------------------------------------------------------------
def _gemini_model_name():
    return os.getenv("GEMINI_MODEL") or os.getenv("GEMINI_DEFAULT_MODEL") or "gemini-2.5-flash"


def _parse_json_payload(text):
    """Nhận JSON từ Gemini (tolerate ```json fence / text thừa). Trả về dict hoặc None."""
    if not text:
        return None
    s = text.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)
    s = s.strip()
    if not s.startswith("{"):
        start = s.find("{")
        end = s.rfind("}")
        if start == -1 or end <= start:
            return None
        s = s[start:end + 1]
    try:
        obj = json.loads(s)
    except ValueError:
        return None
    return obj if isinstance(obj, dict) else None


def gemini_diagnose(image_bytes, mime, context_text="", model_version=MODEL_V3):
    """
    Gửi ảnh (base64 trên wire) + prompt tới Gemini API, nhận JSON phân tích.
    Ném DiagnosisUnavailable khi thiếu key / lỗi mạng / JSON hỏng.
    """
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise DiagnosisUnavailable(
            "Dịch vụ AI chưa được cấu hình (thiếu biến GEMINI_API_KEY). "
            "Vui lòng liên hệ quản trị hệ thống."
        )

    prompt = build_diagnosis_prompt(context_text, model_version)
    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
        )
        response = client.models.generate_content(
            model=_gemini_model_name(),
            # Part.from_bytes: SDK tự mã hoá bytes -> base64 (inline_data) khi gửi lên API
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime),
                prompt,
            ],
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
                max_output_tokens=GEMINI_MAX_OUTPUT_TOKENS,
            ),
        )
        text = (getattr(response, "text", None) or "").strip()
    except DiagnosisUnavailable:
        raise
    except Exception as e:
        logger.exception("Gọi Gemini vision thất bại")
        raise DiagnosisUnavailable(
            "Không kết nối được dịch vụ AI. Vui lòng thử lại sau."
        ) from e

    payload = _parse_json_payload(text)
    if payload is None:
        logger.warning("Gemini trả JSON không hợp lệ (dài %d ký tự)", len(text))
        raise DiagnosisUnavailable("Dịch vụ AI trả về kết quả không hợp lệ. Vui lòng thử lại.")
    return payload


# --------------------------------------------------------------------------------------
# Chuẩn hoá kết quả -> contract FE
# --------------------------------------------------------------------------------------
def severity_of(probability):
    """Ngưỡng thống nhất với FE: >=60 Nghiêm trọng, >=35 Trung bình, còn lại Nhẹ."""
    if probability >= 60:
        return "Nghiêm trọng"
    if probability >= 35:
        return "Trung bình"
    return "Nhẹ"


def _badge_class_for(severity):
    return {"Nghiêm trọng": "badge-high", "Trung bình": "badge-mid"}.get(severity, "badge-low")


def _clamp_percent(value):
    """Chuỗi '87%', '87,5', 150... -> số 0..100 hoặc None nếu không đọc được."""
    if value is None or isinstance(value, bool):
        return None
    try:
        p = float(str(value).replace("%", "").replace(",", ".").strip())
    except (TypeError, ValueError):
        return None
    if p != p:  # NaN
        return None
    return max(0.0, min(100.0, p))


def _normalize_class(raw):
    """Chuẩn hoá mã bệnh về đúng key TOMATO_DISEASES; None nếu không hợp lệ."""
    if not isinstance(raw, str):
        return None
    c = raw.strip().replace(" ", "_")
    if c in TOMATO_DISEASES:
        return c
    lower = c.lower()
    for key in TOMATO_DISEASES:
        if key.lower() == lower:
            return key
    return None


def fallback_detections(items, img_width=640, img_height=640):
    """
    Sinh bbox mặc định theoslot (dùng khi Gemini không trả regions) —
    giữ nguyên bố cục của hàm _generate_bounding_boxes cũ để FE không phải đổi code.
    """
    slot_fractions = [
        (0.15, 0.18, 0.32, 0.28),
        (0.52, 0.22, 0.35, 0.30),
        (0.32, 0.55, 0.38, 0.32),
        (0.12, 0.48, 0.28, 0.26),
    ]
    boxes = []
    for i, item in enumerate(items or []):
        cls = item.get("class") if isinstance(item, dict) else None
        cls = _normalize_class(cls)
        if not cls:
            continue
        info = TOMATO_DISEASES[cls]
        prob = _clamp_percent(item.get("probability")) or 0.0
        fx, fy, fw, fh = slot_fractions[i % len(slot_fractions)]
        boxes.append({
            "class": cls,
            "name_vi": info["name_vi"],
            "confidence": round(prob / 100.0, 2),
            "probability_percent": round(prob, 1),
            "color": info.get("color", "#ea580c"),
            "bbox": [
                int(img_width * fx), int(img_height * fy),
                int(img_width * fw), int(img_height * fh),
            ],
        })
    return boxes


def _detections_from_regions(regions, size):
    """Chuyển regions của Gemini (thang 0-1000) sang bbox pixel theo kích thước ảnh thật."""
    w, h = size
    if not isinstance(regions, list):
        return []
    boxes = []
    seen = set()
    for reg in regions:
        if len(boxes) >= 4:
            break
        if not isinstance(reg, dict):
            continue
        cls = _normalize_class(reg.get("class"))
        if not cls or cls in seen:
            continue
        bbox = reg.get("bbox")
        if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
            continue
        try:
            x = float(bbox[0]) / 1000.0 * w
            y = float(bbox[1]) / 1000.0 * h
            bw = float(bbox[2]) / 1000.0 * w
            bh = float(bbox[3]) / 1000.0 * h
        except (TypeError, ValueError):
            continue
        if bw <= 0 or bh <= 0:
            continue
        # clamp trong khung ảnh
        x = min(max(0.0, x), max(0.0, w - 1))
        y = min(max(0.0, y), max(0.0, h - 1))
        bw = min(bw, w - x)
        bh = min(bh, h - y)
        if bw < 1 or bh < 1:
            continue

        try:
            conf = float(reg.get("confidence"))
        except (TypeError, ValueError):
            conf = 0.5
        if conf > 1.0:
            conf = conf / 100.0
        conf = max(0.0, min(1.0, conf))

        info = TOMATO_DISEASES[cls]
        boxes.append({
            "class": cls,
            "name_vi": info["name_vi"],
            "confidence": round(conf, 2),
            "probability_percent": round(conf * 100, 1),
            "color": info.get("color", "#ea580c"),
            "bbox": [int(round(x)), int(round(y)), int(round(bw)), int(round(bh))],
        })
        seen.add(cls)
    return boxes


def render_basic_report(diseases, healthy):
    """Báo cáo HTML tối giản do server tự sinh — dùng khi Gemini không trả report_html."""
    if healthy or not diseases:
        return (
            '<div class="callout callout-info"><strong>Lá không phát hiện dấu hiệu bệnh.</strong> '
            'Hãy tiếp tục thăm vườn 2 lần mỗi tuần, chú ý mặt dưới lá già sau những ngày mưa ẩm.</div>'
        )
    rows = []
    for d in diseases:
        info = TOMATO_DISEASES[d["class"]]
        sev = severity_of(d["probability"])
        rows.append(
            "<tr><td>{name}</td><td><span class=\"pct\">{p}%</span></td>"
            "<td><span class=\"badge {badge}\">{sev}</span></td></tr>".format(
                name=info["name_vi"], p=d["probability"],
                badge=_badge_class_for(sev), sev=sev,
            )
        )
    primary = diseases[0]
    pinfo = TOMATO_DISEASES[primary["class"]]
    return (
        "<h3>Kết luận nhanh</h3>"
        "<p>Bệnh chính: <strong>{name}</strong> "
        "<span class=\"pct\">{p}%</span> "
        "<span class=\"badge {badge}\">{sev}</span></p>"
        "<h3>Bệnh chính và mức độ</h3>"
        "<table class=\"report-table\"><thead><tr>"
        "<th>Bệnh</th><th>Độ tin cậy</th><th>Mức độ</th></tr></thead>"
        "<tbody>{rows}</tbody></table>"
        "<div class=\"callout callout-warn\">AI chỉ hỗ trợ chẩn đoán sơ bộ — "
        "hãy tham khảo chuyên gia nông nghiệp hoặc trung tâm bảo vệ thực vụ trước khi phun thuốc.</div>"
    ).format(
        name=pinfo["name_vi"], p=primary["probability"],
        badge=_badge_class_for(severity_of(primary["probability"])),
        sev=severity_of(primary["probability"]),
        rows="".join(rows),
    )


def build_analysis(payload, data, model_version=MODEL_V3):
    """
    Chuẩn hoá JSON của Gemini thành contract FE (giữ nguyên shape của api_diagnose cũ):
    primary_disease / secondary_diseases / detections / result / report_html...
    Ném DiagnosisUnavailable nếu payload thiếu dữ liệu chẩn đoán.
    """
    if not isinstance(payload, dict):
        raise DiagnosisUnavailable("Kết quả AI không hợp lệ.")

    raw_diseases = payload.get("diseases")
    if not isinstance(raw_diseases, list):
        raw_diseases = []

    diseases = []
    seen = set()
    for item in raw_diseases[:8]:
        if not isinstance(item, dict):
            continue
        cls = _normalize_class(item.get("class"))
        if not cls or cls in seen:
            continue
        prob = _clamp_percent(item.get("probability"))
        if prob is None:
            continue
        diseases.append({"class": cls, "probability": round(prob, 1)})
        seen.add(cls)
    diseases.sort(key=lambda d: -d["probability"])
    diseases = diseases[:3]

    healthy = bool(payload.get("healthy"))
    if diseases:
        healthy = False
    elif not healthy:
        # Không có bệnh nào AND không khẳng định khỏe mạnh -> payload hỏng
        raise DiagnosisUnavailable("AI không trả về kết quả chẩn đoán hợp lệ.")

    size = image_size(data)

    report_html = sanitize_report_html(payload.get("report_html"))
    if not report_html:
        report_html = render_basic_report(diseases, healthy)

    primary = None
    secondary = []
    if diseases:
        p = diseases[0]
        pinfo = TOMATO_DISEASES[p["class"]]
        primary = {
            "class": p["class"],
            "name_en": pinfo["name_en"],
            "name_vi": pinfo["name_vi"],
            "probability": p["probability"],
            "severity": severity_of(p["probability"]),
            "color": pinfo.get("color", "#ea580c"),
            "treatment": pinfo.get("treatment", {}),
            "prevention": pinfo.get("prevention", ""),
        }
        for s in diseases[1:]:
            sinfo = TOMATO_DISEASES[s["class"]]
            secondary.append({
                "class": s["class"],
                "name_en": sinfo["name_en"],
                "name_vi": sinfo["name_vi"],
                "probability": s["probability"],
                "severity": severity_of(s["probability"]),
                "color": sinfo.get("color", "#ef4444"),
            })

    detections = []
    if not healthy:
        detections = _detections_from_regions(payload.get("regions"), size)
        if not detections and diseases:
            detections = fallback_detections(diseases, size[0], size[1])

    is_coinfection = len(diseases) > 1
    result = [{"class": d["class"], "probability": d["probability"]} for d in diseases]
    treatment_summary = json.dumps((primary or {}).get("treatment", {}), ensure_ascii=False)

    return {
        "analysis_unavailable": False,
        "healthy": healthy,
        "note": "",
        "diseases": diseases,
        "primary_disease": primary,
        "secondary_diseases": secondary,
        "detections": detections,
        "lesion_count": len(detections),
        "is_coinfection": is_coinfection,
        "result": result,
        "report_html": report_html,
        "confidence": (primary or {}).get("probability", 0.0),
        "severity": (primary or {}).get("severity", "Khỏe" if healthy else ""),
        "treatment_summary": treatment_summary,
        "model_version": model_version if model_version in VALID_MODELS else MODEL_V3,
    }


def unavailable_analysis(message=""):
    """Shape phản hồi khi không phân tích được — FE hiển thị `note` thay vì đoán bừa."""
    note = (message or "").strip() or "Dịch vụ AI đang gián đoạn. Vui lòng thử lại sau."
    return {
        "analysis_unavailable": True,
        "healthy": False,
        "note": note,
        "diseases": [],
        "primary_disease": None,
        "secondary_diseases": [],
        "detections": [],
        "lesion_count": 0,
        "is_coinfection": False,
        "result": [],
        "report_html": None,
        "confidence": 0.0,
        "severity": "",
        "treatment_summary": "",
    }


def analyze_record(record, fallback_bytes=None, context_text="", model_version=MODEL_V3):
    """
    Toàn bộ pipeline 1 lần chẩn đoán: link ảnh từ DB -> bytes -> Gemini -> analysis dict.
    Ném DiagnosisUnavailable (message tiếng Việt) khi không phân tích được.
    """
    data, url = load_image_via_db_link(record, fallback_bytes=fallback_bytes)
    data, mime = _ensure_supported_image(data, url)
    payload = gemini_diagnose(data, mime, context_text=context_text, model_version=model_version)
    return build_analysis(payload, data, model_version=model_version)


def run_diagnosis_for_record(record, fallback_bytes=None, context_text="", model_version=MODEL_V3):
    """Best-effort: KHÔNG BAO GIỜ ném exception — lỗi → unavailable_analysis(note)."""
    try:
        return analyze_record(
            record,
            fallback_bytes=fallback_bytes,
            context_text=context_text,
            model_version=model_version,
        )
    except DiagnosisUnavailable as e:
        logger.warning("Chẩn đoán không khả dụng (record=%s): %s",
                       getattr(record, "id", None), e)
        return unavailable_analysis(str(e))
    except Exception:
        logger.exception("Lỗi không xác định khi chẩn đoán (record=%s)",
                         getattr(record, "id", None))
        return unavailable_analysis("Đã có lỗi khi phân tích ảnh. Vui lòng thử lại sau.")


def apply_analysis(record, analysis):
    """
    Ghi kết quả analysis vào bản ghi Leaf_image. Trả về True nếu ghi thành công;
    bỏ qua (return False) khi analysis là unavailable hoặc record None.
    """
    if record is None or not analysis or analysis.get("analysis_unavailable"):
        return False

    primary = analysis.get("primary_disease") or {}
    try:
        record.result = analysis.get("result") or []
        record.detections = analysis.get("detections") or []
        record.primary_disease = primary.get("class", "") or ""
        record.primary_disease_vi = primary.get("name_vi", "") or ""
        record.confidence = float(primary.get("probability") or 0.0)
        record.severity = primary.get("severity") or (
            "Khỏe" if analysis.get("healthy") else ""
        )
        record.is_coinfection = bool(analysis.get("is_coinfection"))
        record.secondary_diseases = analysis.get("secondary_diseases") or []
        record.treatment_summary = analysis.get("treatment_summary") or ""
        if analysis.get("report_html"):
            record.explain = analysis["report_html"]
        record.save()
        return True
    except Exception:
        logger.exception("Không ghi được kết quả chẩn đoán (record=%s)",
                         getattr(record, "id", None))
        return False


# Báo cáo tĩnh khi dịch vụ AI không tạo được report — FE hiển thị nguyên khối
FALLBACK_REPORT_HTML = (
    '<div class="callout callout-warn"><strong>Chưa tạo được báo cáo AI.</strong> '
    'Dịch vụ phân tích đang gián đoạn hoặc chưa được cấu hình — bạn thử lại sau ít phút nhé.</div>'
    '<p>Trong lúc chờ, hãy mô tả triệu chứng (màu vết bệnh, mặt trên/mặt dưới lá, '
    'độ ẩm quanh vườn) cho trợ lý AI để được tư vấn bước đầu.</p>'
)

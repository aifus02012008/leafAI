import base64
import json
import logging
import os
import re

import bleach
import markdown2
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.validators import validate_email
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods, require_POST
from google import genai

from .fastapi import AIServerError, MODEL_V3, VALID_MODELS, fast_api
from .models import *

logger = logging.getLogger(__name__)

# Giới hạn upload ảnh
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_IMAGE_TYPES = ("image/jpeg", "image/png", "image/webp", "image/bmp", "image/gif")

ALLOWED_MD_TAGS = [
    'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'p', 'pre',
    'strong', 'ul', 'br', 'hr', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
]
ALLOWED_MD_ATTRS = {'a': ['href', 'title', 'rel', 'target']}


def sanitize_markdown(text):
    """Markdown -> HTML an toàn (whitelist tag/attr)."""
    if not text:
        return ''
    try:
        raw_html = markdown2.markdown(text)
        clean = bleach.clean(
            raw_html, tags=ALLOWED_MD_TAGS, attributes=ALLOWED_MD_ATTRS,
            protocols=['http', 'https', 'mailto'],
        )
        return bleach.linkify(clean)
    except Exception:
        logger.exception("sanitize_markdown failed")
        return ''


@require_http_methods(["GET", "HEAD"])
def health(request):
    return JsonResponse({"status": "ok"})


def _validate_image_bytes(img_bytes, content_type=None):
    """Kiểm tra ảnh upload: kích thước + MIME. Trả về thông báo lỗi hoặc None."""
    if not img_bytes:
        return _("Không có dữ liệu ảnh")
    if len(img_bytes) > MAX_IMAGE_SIZE:
        return _("Ảnh vượt quá giới hạn 10MB")
    if content_type and not content_type.startswith("image/"):
        return _("File không phải là ảnh hợp lệ")
    return None


def _run_diagnosis(request, img_bytes, file_name):
    """Gọi AI server, lưu kết quả.

    Trả về (skin_img, error_message): chỉ một trong hai khác None.
    """
    # Kiểm tra MIME theo phần mở rộng file
    ext = os.path.splitext(file_name or '')[1].lower()
    if ext in ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif', ''):
        pass
    else:
        return None, _("Định dạng ảnh không được hỗ trợ")

    image_b64 = base64.b64encode(img_bytes).decode("utf-8")

    model_version = request.POST.get('model_version') or MODEL_V3
    if model_version not in VALID_MODELS:
        model_version = MODEL_V3

    # chống lặp máy gọi AI liên tục
    if _throttled(f"upload:{request.user.id}", limit=10, seconds=60):
        raise Throttled(_("Bạn đang gửi quá nhiều yêu cầu. Vui lòng chờ ít phút rồi thử lại."))

    try:
        output = fast_api(image_b64, model_version=model_version)
    except AIServerError as e:
        logger.error("AI server error: %s", e)
        return None, _("Không thể kết nối dịch vụ chẩn đoán. Vui lòng thử lại sau.")

    heat_b64 = output.get('heatmap_base64')
    heatmap_file = None
    if heat_b64:
        try:
            heatmap_file = ContentFile(
                base64.b64decode(heat_b64), name="heatmap_" + (file_name or 'capture.jpg'))
        except Exception:
            logger.warning("Không decode được heatmap base64")
            heatmap_file = None

    image_file = ContentFile(img_bytes, name=file_name)

    skin_img = Leaf_image.objects.create(
        image=image_file,
        result=output.get('results'),
        heatmap=heatmap_file,
        user=Profile.objects.get(user=request.user),
        more='',
    )
    return skin_img, None


@login_required
def upload_file(request):
    """Upload ảnh từ file (modal)."""
    if request.method != "POST":
        return JsonResponse({"error": _("Chỉ hỗ trợ POST")}, status=405)

    uploaded_file = request.FILES.get("image")
    if not uploaded_file:
        return JsonResponse({"error": _("Không có dữ liệu ảnh")}, status=400)

    img_bytes = uploaded_file.read()
    err = _validate_image_bytes(img_bytes, content_type=uploaded_file.content_type)
    if err:
        return JsonResponse({"error": err}, status=400)

    file_name = uploaded_file.name or "upload.jpg"
    try:
        skin_img, error = _run_diagnosis(request, img_bytes, file_name)
    except Throttled as e:
        return JsonResponse({"error": e.message}, status=429)
    if error:
        return JsonResponse({"error": error}, status=502)
    return redirect('result', image_id=skin_img.id)


@login_required
def upload_image(request):
    """Upload ảnh từ camera capture (base64 trong POST)."""
    if request.method != "POST":
        return JsonResponse({"error": _("Chỉ hỗ trợ POST")}, status=405)

    image_data = request.POST.get("image")
    if not image_data:
        return JsonResponse({"error": _("Không có dữ liệu ảnh")}, status=400)

    # Bỏ header base64 (data:image/...;base64,)
    match = re.match(r"^data:image/[\w.+-]+;base64,(.+)$", image_data, flags=re.DOTALL)
    if match:
        b64_part = match.group(1)
        file_name = "leaf_capture.jpg"
    else:
        b64_part = image_data
        file_name = "leaf_capture.jpg"

    try:
        img_bytes = base64.b64decode(b64_part, validate=True)
    except Exception:
        return JsonResponse({"error": _("Dữ liệu ảnh base64 không hợp lệ")}, status=400)

    err = _validate_image_bytes(img_bytes, content_type="image/jpeg")
    if err:
        return JsonResponse({"error": err}, status=400)

    try:
        skin_img, error = _run_diagnosis(request, img_bytes, file_name)
    except Throttled as e:
        return JsonResponse({"error": e.message}, status=429)
    if error:
        return JsonResponse({"error": error}, status=502)
    return redirect('result', image_id=skin_img.id)


class Throttled(Exception):
    """Yêu cầu bị rate-limit."""
    def __init__(self, message):
        super().__init__(message)
        self.message = message


def _throttled(key, limit, seconds):
    """Đếm đơn giản bằng cache. Trả về True nếu vượt limit."""
    try:
        hits = cache.get(key, 0)
        if hits >= limit:
            return True
        cache.set(key, hits + 1, seconds)
    except Exception:
        logger.warning("cache throttle unavailable")
    return False


@login_required
def chatbot_api(request):
    """POST JSON {message} -> {reply, reply_html}."""
    if request.method != 'POST':
        return JsonResponse({"error": _("Chỉ hỗ trợ POST")}, status=405)

    try:
        body = json.loads(request.body.decode('utf-8'))
        message = (body.get('message') or '').strip()
        if not message:
            return JsonResponse({"error": _("Thiếu trường 'message'")}, status=400)
        if len(message) > 4000:
            return JsonResponse({"error": _("Tin nhắn quá dài (tối đa 4000 ký tự)")}, status=400)

        # chống lạm dụng gọi Gemini (chi phí API)
        if _throttled(f"chatbot:{request.user.id}", limit=20, seconds=60):
            return JsonResponse(
                {"error": _("Bạn gửi quá nhanh. Vui lòng chờ khoảng 1 phút rồi thử lại.")},
                status=429,
            )

        reply = call_gemini(message, user=request.user)
        if not isinstance(reply, str) or not reply:
            reply = _("Xin lỗi, dịch vụ AI hiện đang gặp sự cố. Vui lòng thử lại sau.")

        max_len = 16000
        if len(reply) > max_len:
            reply = reply[:max_len] + "\n\n...[truncated]"

        return JsonResponse({"reply": reply, "reply_html": sanitize_markdown(reply)})
    except json.JSONDecodeError:
        return JsonResponse({"error": _("JSON không hợp lệ")}, status=400)
    except Exception:
        logger.exception("chatbot_api error")
        return JsonResponse({"error": _("Đã xảy ra lỗi máy chủ")}, status=500)


def call_gemini(prompt, user=None):
    """Gọi Gemini; luôn trả về str (fallback khi lỗi)."""
    api_key = os.getenv('GEMINI_API_KEY')
    fallback = _("Xin chào! Dịch vụ AI hiện đang tạm thời gián đoạn, bạn vui lòng thử lại sau nhé.")

    if not api_key:
        return f"[DEV REPLY] {prompt[:400]}"

    model = os.getenv('GEMINI_MODEL') or os.getenv('GEMINI_DEFAULT_MODEL') or 'gemini-2.5-flash-lite'
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model, contents=prompt)
        text = getattr(response, 'text', None)
        return text if text else fallback
    except Exception:
        logger.exception("Gemini call failed")
        return fallback


def login_view(request):
    if request.method == 'POST':
        identifier = (request.POST.get('username') or request.POST.get('email') or '').strip()
        password = request.POST.get('password') or ''

        user = authenticate(request, username=identifier, password=password)
        if user is None and '@' in identifier:
            # cho phép đăng nhập bằng email
            from django.contrib.auth.models import User
            candidate = User.objects.filter(email__iexact=identifier).first()
            if candidate:
                user = authenticate(request, username=candidate.username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        messages.error(request, _("Tên đăng nhập hoặc mật khẩu không chính xác."))
        return render(request, 'login.html', {'data': request.POST})
    return render(request, 'login.html')


def signup_view(request):
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip()
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        avatar = request.FILES.get('avatar')
        birth_date = request.POST.get('birth_date')

        if not username or not email or not password:
            messages.error(request, _("Vui lòng điền đầy đủ thông tin."))
            return render(request, 'signup.html', {'data': request.POST})

        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, _("Email không hợp lệ."))
            return render(request, 'signup.html', {'data': request.POST})

        if User.objects.filter(username=username).exists():
            messages.error(request, _("Tên đăng nhập đã tồn tại."))
            return render(request, 'signup.html', {'data': request.POST})

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, _("Email đã được sử dụng."))
            return render(request, 'signup.html', {'data': request.POST})

        try:
            validate_password(password)
        except ValidationError as e:
            messages.error(request, " ".join(e.messages))
            return render(request, 'signup.html', {'data': request.POST})

        try:
            user = User.objects.create_user(
                username=username, email=email, password=password)

            profile, _created = Profile.objects.get_or_create(user=user)
            if birth_date:
                profile.birth_date = birth_date
            if avatar:
                profile.avatar = avatar
            profile.save()

            # nhiều auth backend -> phải chỉ định backend khi login trực tiếp
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
        except Exception:
            logger.exception("signup error")
            messages.error(request, _("Đã xảy ra lỗi trong quá trình đăng ký."))
            return render(request, 'signup.html', {'data': request.POST})

    return render(request, 'signup.html')


@login_required
def home_view(request):
    return render(request, 'home.html')


@login_required
def result_view(request, image_id):
    skin_image = get_object_or_404(
        Leaf_image, id=image_id, user__user=request.user)
    return render(request, 'result.html', {'skin_image': skin_image})


@login_required
def chatbot_view(request):
    return render(request, 'chatbot.html')


def pharmacy_view(request):
    """Bản đồ cơ sở vật tư / cửa hàng vật tư nông nghiệp gần tôi."""
    return render(request, 'pharmacy.html')


@login_required
def your_profile(request):
    profile = get_object_or_404(Profile, user=request.user)
    classifications = Leaf_image.objects.filter(
        user=profile).order_by('-uploaded_at')
    return render(request, 'profile.html', {'profile': profile, 'classifications': classifications})


@login_required
@require_POST
def delete_classification(request, image_id):
    """Xóa 1 bản ghi lịch sử chẩn đoán (chỉ của chính mình)."""
    image = get_object_or_404(Leaf_image, id=image_id, user__user=request.user)
    # xóa file trên storage trước khi xóa record
    for field in ('image', 'heatmap'):
        f = getattr(image, field)
        if f:
            try:
                f.delete(save=False)
            except Exception:
                logger.warning("Không xóa được file %s", field)
    image.delete()
    messages.success(request, _("Đã xóa bản ghi chẩn đoán."))
    return redirect('your_profile')


@login_required
def predict(request, id):
    """Chẩn đoán nâng cao: nhận thông tin người dùng + gọi Gemini tạo báo cáo."""
    image = get_object_or_404(Leaf_image, id=id, user__user=request.user)

    if request.method != "POST":
        return redirect('result', image_id=image.id)

    # Form gửi gender/age/symptom/illness_history/drug_history
    gender = (request.POST.get('gender') or '').strip()
    age = (request.POST.get('age') or '').strip()
    symptom = (request.POST.get('symptom') or '').strip()
    illness_history = (request.POST.get('illness_history') or '').strip()
    drug_history = (request.POST.get('drug_history') or '').strip()
    # backward-compat với client cũ
    more_information = (request.POST.get('more_information') or '').strip()

    image.gender = gender[:10]
    image.age = age[:10]
    image.symptom = symptom
    image.illness_history = illness_history
    image.drug_history = drug_history
    image.more = more_information or "\n".join(filter(None, [
        f"Giới tính: {gender}" if gender else "",
        f"Độ tuổi: {age}" if age else "",
        f"Triệu chứng: {symptom}" if symptom else "",
        f"Tiền sử bệnh: {illness_history}" if illness_history else "",
        f"Tiền sử thuốc: {drug_history}" if drug_history else "",
    ]))
    image.save()

    prompt = f"""
        Bạn là một chuyên gia hỗ trợ phân tích bệnh cây trồng.
        DỮ LIỆU ĐẦU VÀO:
        - Kết quả từ mô hình (JSON): {json.dumps(image.result, ensure_ascii=False) if image.result else '{}'}
        - Thông tin bổ sung từ người dùng: {image.more}

        YÊU CẦU QUAN TRỌNG: Phân tích tình trạng và trả về kết quả dưới định dạng JSON duy nhất, không có văn bản thừa bên ngoài.
        Cấu trúc JSON yêu cầu:
        {{
            "vi": "Nội dung phân tích chi tiết bằng tiếng Việt...",
            "en": "Detailed analysis content in English..."
        }}

        HƯỚNG DẪN NỘI DUNG (Áp dụng cho cả 2 ngôn ngữ):
        1. Đoạn 1 - Nhận diện tình trạng: Giải thích kết quả mô hình, cho biết hệ thống nghiêng về khả năng nào nhất.
        2. Đoạn 2 - Phân tích nguyên nhân: Liên hệ tổn thương lá cây với các thông tin khác.
        3. Đoạn 3 - Hướng dẫn theo dõi: Các bước kiểm tra lâm sàng đơn giản tại nhà.
        4. Đoạn 4 - Lời khuyên & Hành động: Khuyên nhờ sự trợ giúp của chuyên gia nông nghiệp, nhấn mạnh AI không thay thế chuyên gia.

        LƯU Ý: Không dùng Markdown phức tạp (#), chỉ dùng văn bản thuần, xuống dòng rõ ràng giữa các đoạn.
    """
    raw_reply = call_gemini(prompt, user=request.user)

    try:
        json_str = re.sub(r'^```json\s*|\s*```$', '', raw_reply.strip(), flags=re.MULTILINE)
        content_data = json.loads(json_str)
        reply_vi = content_data.get('vi', '') or raw_reply
    except Exception:
        logger.warning("Gemini không trả JSON hợp lệ, dùng text thô")
        reply_vi = raw_reply

    image.explain = sanitize_markdown(reply_vi)
    image.save()
    return redirect('result', image_id=image.id)


def logout_view(request):
    logout(request)
    return redirect('login')

# -*- coding: utf-8 -*-
import base64
import io
import json
import tempfile
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import NoReverseMatch, reverse
from PIL import Image as PILImage

from .leaf_ai import (
    DiagnosisUnavailable,
    FALLBACK_REPORT_HTML,
    build_analysis,
    load_image_via_db_link,
    run_diagnosis_for_record,
    sanitize_report_html,
    unavailable_analysis,
)
from .models import Leaf_image, Profile

TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# 1x1 PNG hợp lệ
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def make_png_bytes(width=400, height=300, color=(34, 139, 34)):
    """PNG kích thước thật để test bbox quy đổi theo kích thước ảnh."""
    buf = io.BytesIO()
    PILImage.new("RGB", (width, height), color).save(buf, format="PNG")
    return buf.getvalue()


PNG_400 = make_png_bytes()


# Payload giả lập Gemini trả về (đúng schema leaf_ai yêu cầu)
GEMINI_PAYLOAD = {
    "healthy": False,
    "diseases": [
        {"class": "Anthracnose", "probability": 87},
        {"class": "Downy_blight", "probability": 42},
    ],
    "regions": [
        {"class": "Anthracnose", "confidence": 0.9, "bbox": [40, 30, 200, 150]},
    ],
    "report_html": (
        '<h3>Kết luận nhanh</h3>'
        '<p>Thán thư <span class="pct">87%</span> '
        '<span class="badge badge-high">Nghiêm trọng</span></p>'
        '<script>alert("xss")</script>'
        '<table class="report-table"><thead><tr><th>Bệnh</th><th>Độ tin cậy</th></tr></thead>'
        "<tbody><tr><td>Thán thư</td><td>87%</td></tr></tbody></table>"
    ),
}


def fake_analysis(**overrides):
    """Analysis dict đầy đủ (cùng shape với leaf_ai.build_analysis) cho mock."""
    analysis = build_analysis(dict(GEMINI_PAYLOAD), PNG_400, "v3")
    analysis.update(overrides)
    return analysis


def make_profile(username="tester", email="t@e.com"):
    user = User.objects.create_user(username=username, email=email, password="Str0ng!Pass99")
    profile, _ = Profile.objects.get_or_create(user=user)
    return user, profile


@override_settings(STORAGES=TEST_STORAGES, MEDIA_ROOT=tempfile.mkdtemp())
class HealthTests(TestCase):
    def test_health_ok(self):
        resp = self.client.get("/health/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")


class UrlNameTests(TestCase):
    """Mọi {% url %} dùng trong template phải reverse được (bug P0 pharmacy trước đây)."""

    def test_all_template_url_names_reverse(self):
        names_and_args = [
            ("home", []), ("upload_image", []), ("login", []), ("logout", []),
            ("signup", []), ("chatbot", []), ("chatbot_api", []), ("result", [1]),
            ("your_profile", []), ("upload_file", []), ("predict", [1]),
            ("delete_classification", [1]), ("health", []),
        ]
        for name, args in names_and_args:
            try:
                reverse(name, args=args)
            except NoReverseMatch:
                self.fail(f"URL name '{name}' không reverse được")


class AdminImportTests(TestCase):
    def test_admin_module_loads(self):
        """Bug P0 cũ: admin.py register Post/Comment không tồn tại -> NameError lúc boot."""
        import importlib
        mod = importlib.import_module("Dermal.admin")
        self.assertTrue(mod)


@override_settings(STORAGES=TEST_STORAGES, MEDIA_ROOT=tempfile.mkdtemp())
class AuthTests(TestCase):
    def test_signup_login_logout(self):
        resp = self.client.post("/signup/", {
            "username": "alice", "email": "alice@example.com", "password": "Str0ng!Pass99",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(User.objects.filter(username="alice").exists())

        self.client.logout()
        resp = self.client.post("/login/", {
            "username": "alice", "password": "Str0ng!Pass99",
        })
        self.assertEqual(resp.status_code, 302)

    def test_login_by_email(self):
        make_profile("bob", "bob@example.com")
        resp = self.client.post("/login/", {
            "username": "bob@example.com", "password": "Str0ng!Pass99",
        })
        self.assertEqual(resp.status_code, 302)

    def test_login_wrong_password(self):
        make_profile("carol", "carol@example.com")
        resp = self.client.post("/login/", {
            "username": "carol", "password": "wrongpass",
        })
        self.assertEqual(resp.status_code, 200)  # render lại login.html
        self.assertFalse(resp.context["user"].is_authenticated)

    def test_home_requires_login(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp.url)

    def test_signup_rejects_weak_password(self):
        resp = self.client.post("/signup/", {
            "username": "weak", "email": "weak@example.com", "password": "123",
        }, follow=False)
        self.assertEqual(resp.status_code, 200)  # render lại signup với lỗi
        self.assertFalse(User.objects.filter(username="weak").exists())


@override_settings(STORAGES=TEST_STORAGES, MEDIA_ROOT=tempfile.mkdtemp())
class UploadTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()  # tránh rate-limit của test trước ảnh hưởng test này
        self.user, self.profile = make_profile()
        self.client.force_login(self.user)

    @patch("Dermal.views.run_diagnosis_for_record")
    def test_upload_file_success(self, m_diag):
        """Upload -> lưu ảnh vào DB -> chẩn đoán best-effort -> redirect kết quả."""
        m_diag.return_value = fake_analysis()
        resp = self.client.post("/upload/file/", {
            "image": SimpleUploadedFile("leaf.png", TINY_PNG, content_type="image/png"),
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Leaf_image.objects.count(), 1)
        m_diag.assert_called_once()

        rec = Leaf_image.objects.get()
        self.assertTrue(rec.explain)  # báo cáo HTML đã lưu
        self.assertEqual(rec.primary_disease, "Anthracnose")
        self.assertTrue(rec.result)  # bảng kết quả có dữ liệu cho template

    @patch("Dermal.views.run_diagnosis_for_record")
    def test_upload_file_rejects_non_image(self, m_diag):
        resp = self.client.post("/upload/file/", {
            "image": SimpleUploadedFile("evil.exe", b"MZ....", content_type="application/x-msdownload"),
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Leaf_image.objects.count(), 0)
        m_diag.assert_not_called()

    @patch("Dermal.views.run_diagnosis_for_record")
    def test_upload_survives_ai_exception(self, m_diag):
        """AI lỗi không xác định -> ảnh vẫn lưu, không 500."""
        m_diag.side_effect = RuntimeError("gemini down")
        resp = self.client.post("/upload/file/", {
            "image": SimpleUploadedFile("leaf.png", TINY_PNG, content_type="image/png"),
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Leaf_image.objects.count(), 1)
        self.assertFalse(Leaf_image.objects.get().explain)

    @patch("Dermal.views.run_diagnosis_for_record")
    def test_upload_ai_unavailable_keeps_record(self, m_diag):
        """Dịch vụ AI không khả dụng (thiếu key...) -> bản ghi vẫn còn để xử lý sau."""
        m_diag.return_value = unavailable_analysis("Thiếu GEMINI_API_KEY")
        resp = self.client.post("/upload/file/", {
            "image": SimpleUploadedFile("leaf.png", TINY_PNG, content_type="image/png"),
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Leaf_image.objects.count(), 1)
        self.assertFalse(Leaf_image.objects.get().explain)

    @patch("Dermal.views.run_diagnosis_for_record")
    def test_upload_image_camera_base64(self, m_diag):
        m_diag.return_value = fake_analysis()
        data_url = "data:image/jpeg;base64," + base64.b64encode(TINY_PNG).decode()
        resp = self.client.post("/upload/", {"image": data_url})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Leaf_image.objects.count(), 1)

    def test_upload_image_invalid_base64(self):
        resp = self.client.post("/upload/", {"image": "data:image/jpeg;base64,!!!not-base64!!!"})
        self.assertEqual(resp.status_code, 400)

    def test_upload_requires_login(self):
        self.client.logout()
        resp = self.client.post("/upload/", {"image": "x"})
        self.assertEqual(resp.status_code, 302)


@override_settings(STORAGES=TEST_STORAGES, MEDIA_ROOT=tempfile.mkdtemp())
class ResultAndHistoryTests(TestCase):
    def setUp(self):
        self.user, self.profile = make_profile()
        self.client.force_login(self.user)
        self.img = Leaf_image.objects.create(
            image=SimpleUploadedFile("l.png", TINY_PNG, content_type="image/png"),
            user=self.profile, result=[{"class": "Anthracnose", "probability": 80.0}],
        )

    def test_result_view_own(self):
        resp = self.client.get(f"/result/{self.img.id}/")
        self.assertEqual(resp.status_code, 200)

    def test_result_view_foreign_404(self):
        other, _ = make_profile("other", "other@e.com")
        # ảnh của user khác truy cập bằng user này -> 404
        other_profile = Profile.objects.get(user=other)
        foreign = Leaf_image.objects.create(
            user=other_profile, result=[], image=SimpleUploadedFile("f.png", TINY_PNG,
                                                                   content_type="image/png"))
        resp = self.client.get(f"/result/{foreign.id}/")
        self.assertEqual(resp.status_code, 404)

    def test_profile_lists_history(self):
        resp = self.client.get("/profile/")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Leaf_images/", status_code=200)

    @patch("Dermal.views.run_diagnosis_for_record")
    def test_predict_saves_extra_info_no_integrity_error(self, m_diag):
        """Bug P0 cũ: more=None -> IntegrityError 500. Predict nay gọi Gemini kèm ảnh từ DB."""
        m_diag.return_value = fake_analysis(report_html="<p>Phân tích VN</p>")
        resp = self.client.post(f"/predict/{self.img.id}/", {
            "gender": "Nam", "age": "30",
            "symptom": "Vàng lá", "illness_history": "Không có",
            "drug_history": "Không có",
        })
        self.assertEqual(resp.status_code, 302)
        self.img.refresh_from_db()
        self.assertEqual(self.img.gender, "Nam")
        self.assertIn("Vàng lá", self.img.more)
        self.assertIn("Phân tích VN", self.img.explain)
        # context (info người dùng) được truyền vào prompt
        m_diag.assert_called_once()
        _, kwargs = m_diag.call_args
        self.assertIn("Vàng lá", kwargs.get("context_text", ""))

    @patch("Dermal.views.run_diagnosis_for_record")
    def test_predict_ai_failure_falls_back(self, m_diag):
        """AI không trả được báo cáo -> explain là HTML thân thiện, không trống, không 500."""
        m_diag.return_value = unavailable_analysis("AI gián đoạn")
        resp = self.client.post(f"/predict/{self.img.id}/", {"symptom": "test"})
        self.assertEqual(resp.status_code, 302)
        self.img.refresh_from_db()
        self.assertTrue(self.img.explain)
        self.assertEqual(self.img.explain, FALLBACK_REPORT_HTML)

    def test_predict_missing_record_404(self):
        resp = self.client.post("/predict/99999/", {"symptom": "x"})
        self.assertEqual(resp.status_code, 404)

    def test_delete_classification(self):
        resp = self.client.post(f"/history/{self.img.id}/delete/")
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Leaf_image.objects.filter(id=self.img.id).exists())

    def test_delete_foreign_404(self):
        other, other_profile = make_profile("zoe", "zoe@e.com")
        foreign = Leaf_image.objects.create(user=other_profile, result=[])
        resp = self.client.post(f"/history/{foreign.id}/delete/")
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(Leaf_image.objects.filter(id=foreign.id).exists())

    def test_delete_rejects_get(self):
        resp = self.client.get(f"/history/{self.img.id}/delete/")
        self.assertEqual(resp.status_code, 405)


@override_settings(STORAGES=TEST_STORAGES, MEDIA_ROOT=tempfile.mkdtemp())
class ChatbotApiTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.user, _ = make_profile()
        self.client.force_login(self.user)

    @patch("Dermal.views.call_gemini")
    def test_chatbot_reply(self, m_gemini):
        m_gemini.return_value = "Chào bạn, đây là **câu trả lời**"
        resp = self.client.post("/chatbot/api/", data=json.dumps({"message": "hello"}),
                                content_type="application/json",
                                HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("câu trả lời", body["reply"])
        self.assertIn("<strong>", body["reply_html"])

    def test_chatbot_empty_message(self):
        resp = self.client.post("/chatbot/api/", data=json.dumps({"message": "  "}),
                                content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    def test_chatbot_invalid_json(self):
        resp = self.client.post("/chatbot/api/", data="not json",
                                content_type="application/json")
        self.assertEqual(resp.status_code, 400)

    def test_chatbot_requires_login(self):
        self.client.logout()
        resp = self.client.post("/chatbot/api/", data=json.dumps({"message": "hi"}),
                                content_type="application/json")
        self.assertEqual(resp.status_code, 302)


@override_settings(STORAGES=TEST_STORAGES, MEDIA_ROOT=tempfile.mkdtemp())
class ThrottleTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.user, self.profile = make_profile()
        self.client.force_login(self.user)

    @patch("Dermal.views.call_gemini")
    def test_chatbot_rate_limited(self, m_gemini):
        m_gemini.return_value = "ok"
        statuses = []
        for i in range(21):
            resp = self.client.post("/chatbot/api/", data=json.dumps({"message": f"hi {i}"}),
                                    content_type="application/json")
            statuses.append(resp.status_code)
        self.assertIn(429, statuses)
        self.assertEqual(statuses.count(200), 20)

    @patch("Dermal.views.run_diagnosis_for_record")
    def test_upload_rate_limited(self, m_diag):
        m_diag.return_value = fake_analysis()
        statuses = []
        for i in range(11):
            resp = self.client.post("/upload/", {
                "image": "data:image/jpeg;base64," + base64.b64encode(TINY_PNG).decode()
            })
            statuses.append(resp.status_code)
        self.assertIn(429, statuses)  # rate-limit
        self.assertEqual(statuses.count(302), 10)


@override_settings(STORAGES=TEST_STORAGES, MEDIA_ROOT=tempfile.mkdtemp())
class DiagnoseApiTests(TestCase):
    """POST /api/diagnose/ — pipeline: lưu ảnh -> link ảnh từ DB -> Gemini -> JSON + báo cáo."""

    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.user, self.profile = make_profile()
        self.client.force_login(self.user)

    @patch("Dermal.api_views.run_diagnosis_for_record")
    def test_diagnose_success(self, m_diag):
        m_diag.return_value = fake_analysis()
        resp = self.client.post("/api/diagnose/", {
            "image": SimpleUploadedFile("leaf.png", PNG_400, content_type="image/png"),
            "model_version": "v3",
        })
        self.assertEqual(resp.status_code, 200)
        body = resp.json()

        self.assertTrue(body["success"])
        self.assertIsNotNone(body["id"])
        self.assertEqual(body["model_version"], "v3")
        self.assertEqual(body["primary_disease"]["class"], "Anthracnose")
        self.assertEqual(body["primary_disease"]["severity"], "Nghiêm trọng")
        self.assertEqual(body["secondary_diseases"][0]["class"], "Downy_blight")
        self.assertTrue(body["is_coinfection"])
        self.assertTrue(body["report_html"])
        self.assertNotIn("<script", body["report_html"])
        self.assertFalse(body["analysis_unavailable"])
        self.assertFalse(body["heatmap_available"])
        self.assertGreaterEqual(len(body["detections"]), 1)

        self.assertEqual(Leaf_image.objects.count(), 1)
        rec = Leaf_image.objects.get()
        self.assertTrue(rec.explain)

        # Pipeline gọi chẩn đoán với record vừa lưu (link ảnh lấy từ DB) + bytes fallback
        m_diag.assert_called_once()
        args, kwargs = m_diag.call_args
        self.assertEqual(args[0].id, rec.id)
        self.assertEqual(kwargs.get("fallback_bytes"), PNG_400)
        self.assertEqual(kwargs.get("model_version"), "v3")

    @patch("Dermal.api_views.run_diagnosis_for_record")
    def test_diagnose_unavailable_returns_note(self, m_diag):
        """AI không khả dụng -> 200 + analysis_unavailable + note, KHÔNG bịa bệnh."""
        m_diag.return_value = unavailable_analysis("Thiếu GEMINI_API_KEY")
        resp = self.client.post("/api/diagnose/", {
            "image": SimpleUploadedFile("leaf.png", PNG_400, content_type="image/png"),
        })
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body["success"])
        self.assertTrue(body["analysis_unavailable"])
        self.assertIsNone(body["primary_disease"])
        self.assertEqual(body["secondary_diseases"], [])
        self.assertIn("GEMINI_API_KEY", body["note"])
        # ảnh vẫn được lưu để người dùng thử lại sau
        self.assertEqual(Leaf_image.objects.count(), 1)

    def test_diagnose_missing_image_400(self):
        resp = self.client.post("/api/diagnose/", {})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("error", resp.json())
        self.assertEqual(Leaf_image.objects.count(), 0)

    @patch("Dermal.api_views.run_diagnosis_for_record")
    def test_diagnose_rate_limited(self, m_diag):
        m_diag.return_value = fake_analysis()
        statuses = []
        for _ in range(11):
            resp = self.client.post("/api/diagnose/", {
                "image": SimpleUploadedFile("leaf.png", TINY_PNG, content_type="image/png"),
            })
            statuses.append(resp.status_code)
        self.assertIn(429, statuses)
        self.assertEqual(statuses.count(200), 10)


class LeafAiTests(TestCase):
    """Unit test module leaf_ai: sanitize HTML, chuẩn hoá payload, đọc link ảnh từ DB."""

    def setUp(self):
        self.user, self.profile = make_profile()

    def test_sanitize_strips_script_and_handlers(self):
        html = (
            '<h3>OK</h3><script>alert(1)</script>'
            '<p onclick="evil()">hi</p><style>.a{color:red}</style>'
            '<table class="report-table"><tr><th>B</th></tr></table>'
        )
        out = sanitize_report_html(html)
        self.assertNotIn("<script", out)
        self.assertNotIn("onclick", out)
        self.assertNotIn("<style", out)
        self.assertIn('class="report-table"', out)

    def test_sanitize_prunes_unknown_classes(self):
        out = sanitize_report_html(
            '<span class="badge badge-high evil">Nghiêm trọng</span>'
            '<div class="dropcap">x</div>'
        )
        self.assertIn("badge-high", out)
        self.assertNotIn("evil", out)
        self.assertNotIn("dropcap", out)

    def test_build_analysis_full(self):
        a = build_analysis(dict(GEMINI_PAYLOAD), PNG_400, "v3")
        self.assertFalse(a["analysis_unavailable"])
        self.assertFalse(a["healthy"])

        p = a["primary_disease"]
        self.assertEqual(p["class"], "Anthracnose")
        self.assertEqual(p["probability"], 87.0)
        self.assertEqual(p["severity"], "Nghiêm trọng")

        self.assertEqual(a["secondary_diseases"][0]["class"], "Downy_blight")
        self.assertEqual(a["secondary_diseases"][0]["severity"], "Trung bình")
        self.assertTrue(a["is_coinfection"])
        self.assertGreaterEqual(a["lesion_count"], 1)

        # bbox đổi từ thang 0-1000 -> pixel theo kích thước ảnh thật (400x300)
        for det in a["detections"]:
            x, y, w, h = det["bbox"]
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            self.assertLessEqual(x + w, 400)
            self.assertLessEqual(y + h, 300)

        self.assertNotIn("<script", a["report_html"])
        self.assertEqual(a["result"][0], {"class": "Anthracnose", "probability": 87.0})

    def test_build_analysis_healthy(self):
        a = build_analysis(
            {"healthy": True, "diseases": [], "regions": [], "report_html": "<p>Lá ổn</p>"},
            PNG_400, "v3",
        )
        self.assertTrue(a["healthy"])
        self.assertIsNone(a["primary_disease"])
        self.assertEqual(a["detections"], [])
        self.assertEqual(a["result"], [])
        self.assertTrue(a["report_html"])

    def test_build_analysis_invalid_payload_raises(self):
        with self.assertRaises(DiagnosisUnavailable):
            build_analysis({"healthy": False, "diseases": []}, PNG_400, "v3")
        # lớp bệnh lạ (không thuộc danh mục bệnh vải thiều Lục Ngạn) bị loại -> rỗng -> không hợp lệ
        with self.assertRaises(DiagnosisUnavailable):
            build_analysis(
                {"healthy": False, "diseases": [{"class": "Human_acne", "probability": 50}]},
                PNG_400, "v3",
            )
        with self.assertRaises(DiagnosisUnavailable):
            build_analysis("not a dict", PNG_400, "v3")

    def test_build_analysis_clamps_and_dedupes(self):
        payload = {
            "healthy": False,
            "diseases": [
                {"class": "anthracnose", "probability": "150%"},
                {"class": "Anthracnose", "probability": "40"},
                {"class": "Downy_blight", "probability": "abc"},
            ],
            "regions": [],
            "report_html": "<p>x</p>",
        }
        a = build_analysis(payload, PNG_400, "v3")
        # lowercase -> chuẩn mã; 150% -> clamp 100; trùng mã -> giữ 1; 'abc' -> loại
        self.assertEqual(a["diseases"], [{"class": "Anthracnose", "probability": 100.0}])

    @override_settings(STORAGES=TEST_STORAGES, MEDIA_ROOT=tempfile.mkdtemp())
    def test_load_image_reads_via_db_link(self):
        """Link tương đối /media/... -> đọc trực tiếp từ storage (không HTTP)."""
        rec = Leaf_image.objects.create(
            image=SimpleUploadedFile("l.png", TINY_PNG, content_type="image/png"),
            user=self.profile,
        )
        data, url = load_image_via_db_link(rec)
        self.assertEqual(data, TINY_PNG)
        self.assertTrue(url.startswith("/media/"), url)

    @patch("Dermal.leaf_ai.requests.get")
    def test_load_image_downloads_http_link(self, m_get):
        """Link tuyệt đối (Cloudinary) -> download qua requests có timeout."""
        m_resp = MagicMock()
        m_resp.iter_content.return_value = [b"jpeg-from-cdn"]
        m_get.return_value = m_resp

        stub = MagicMock()
        stub.image.url = "https://res.cloudinary.com/demo/image/upload/leaf1.jpg"
        data, url = load_image_via_db_link(stub, fallback_bytes=b"unused-fallback")

        self.assertEqual(data, b"jpeg-from-cdn")
        self.assertEqual(url, stub.image.url)
        m_get.assert_called_once()
        self.assertEqual(m_get.call_args[0][0], stub.image.url)
        # fallback không bị dùng khi tải link thành công
        self.assertNotEqual(data, b"unused-fallback")

    @patch("Dermal.leaf_ai.gemini_diagnose")
    def test_run_diagnosis_end_to_end_reads_db_link(self, m_gem):
        """Toàn bộ luồng: record trong DB -> đọc bytes qua link -> gọi Gemini -> analysis."""
        rec = Leaf_image.objects.create(
            image=SimpleUploadedFile("leaf.png", PNG_400, content_type="image/png"),
            user=self.profile,
        )
        m_gem.return_value = dict(GEMINI_PAYLOAD)

        analysis = run_diagnosis_for_record(rec, model_version="v3")
        self.assertFalse(analysis.get("analysis_unavailable"))

        m_gem.assert_called_once()
        args, kwargs = m_gem.call_args
        self.assertEqual(args[0], PNG_400)   # bytes đọc từ DB, không phải upload lần hai
        self.assertEqual(args[1], "image/png")
        self.assertEqual(kwargs.get("model_version"), "v3")

    def test_run_diagnosis_without_image_unavailable(self):
        analysis = run_diagnosis_for_record(None)
        self.assertTrue(analysis["analysis_unavailable"])
        self.assertTrue(analysis["note"])
        self.assertIsNone(analysis["report_html"])

    @patch("Dermal.leaf_ai.gemini_diagnose")
    def test_run_diagnosis_gemini_error_unavailable(self, m_gem):
        m_gem.side_effect = DiagnosisUnavailable("Gemini sập")
        rec = Leaf_image.objects.create(
            image=SimpleUploadedFile("leaf.png", TINY_PNG, content_type="image/png"),
            user=self.profile,
        )
        analysis = run_diagnosis_for_record(rec)
        self.assertTrue(analysis["analysis_unavailable"])
        self.assertEqual(analysis["note"], "Gemini sập")


@override_settings(STORAGES=TEST_STORAGES, MEDIA_ROOT=tempfile.mkdtemp())
class SmokeRenderTests(TestCase):
    """Mọi trang chính phải render 200 (bug P0 cũ: navbar thiếu route -> 500)."""

    def setUp(self):
        self.user, self.profile = make_profile()
        self.client.force_login(self.user)
        self.img = Leaf_image.objects.create(
            image=SimpleUploadedFile("s.png", TINY_PNG, content_type="image/png"),
            user=self.profile, result=[{"class": "Downy_blight", "probability": 91.0}],
            explain="<h3>Kết luận nhanh</h3><p>Báo cáo</p>",
        )

    def test_all_pages_render(self):
        pages = ["/", "/login/", "/signup/", "/chatbot/", "/profile/",
                 f"/result/{self.img.id}/", "/health/"]
        for url in pages:
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200, f"{url} -> {resp.status_code}")

    def test_result_page_renders_report_html(self):
        """Báo cáo HTML phải hiển thị trong container .ai-report (đã sanitize)."""
        resp = self.client.get(f"/result/{self.img.id}/")
        self.assertContains(resp, 'class="ai-report"')
        self.assertContains(resp, "<h3>Kết luận nhanh</h3>")

    def test_admin_login_page(self):
        resp = self.client.get("/admin/login/")
        self.assertEqual(resp.status_code, 200)

import base64
import json
import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import NoReverseMatch, reverse

from .fastapi import AIServerError
from .models import Leaf_image, Profile

TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# 1x1 PNG hợp lệ
TINY_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


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
            ("pharmacy", []), ("delete_classification", [1]), ("health", []),
            ("google_login", []),
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

    @patch("Dermal.views.fast_api")
    def test_upload_file_success(self, m_fast):
        m_fast.return_value = {"results": [{"class": "Early_blight", "probability": 87.5}],
                               "heatmap_base64": None}
        resp = self.client.post("/upload/file/", {
            "image": SimpleUploadedFile("leaf.png", TINY_PNG, content_type="image/png"),
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Leaf_image.objects.count(), 1)
        m_fast.assert_called_once()

    @patch("Dermal.views.fast_api")
    def test_upload_file_rejects_non_image(self, m_fast):
        resp = self.client.post("/upload/file/", {
            "image": SimpleUploadedFile("evil.exe", b"MZ....", content_type="application/x-msdownload"),
        })
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(Leaf_image.objects.count(), 0)
        m_fast.assert_not_called()

    @patch("Dermal.views.fast_api")
    def test_upload_file_ai_server_error(self, m_fast):
        m_fast.side_effect = AIServerError("down")
        resp = self.client.post("/upload/file/", {
            "image": SimpleUploadedFile("leaf.png", TINY_PNG, content_type="image/png"),
        })
        self.assertEqual(resp.status_code, 502)
        self.assertEqual(Leaf_image.objects.count(), 0)

    @patch("Dermal.views.fast_api")
    def test_upload_image_camera_base64(self, m_fast):
        m_fast.return_value = {"results": [{"class": "Late_blight", "probability": 66.0}],
                               "heatmap_base64": None}
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
            user=self.profile, result=[{"class": "Early_blight", "probability": 80.0}],
        )

    def test_result_view_own(self):
        resp = self.client.get(f"/result/{self.img.id}/")
        self.assertEqual(resp.status_code, 200)

    def test_result_view_foreign_404(self):
        other, _ = make_profile("other", "other@e.com")
        resp = self.client.get(f"/result/{self.img.id}/")
        # vẫn là của self.user nên 200; tạo ảnh của user khác và truy cập bằng user này
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

    @patch("Dermal.views.call_gemini")
    def test_predict_saves_extra_info_no_integrity_error(self, m_gemini):
        """Bug P0 cũ: more=None -> IntegrityError 500."""
        m_gemini.return_value = '{"vi": "Phân tích VN", "en": "Analysis EN"}'
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

    @patch("Dermal.views.call_gemini")
    def test_predict_garbled_ai_reply_falls_back(self, m_gemini):
        m_gemini.return_value = "Đây là text thường không phải JSON"
        resp = self.client.post(f"/predict/{self.img.id}/", {"symptom": "test"})
        self.assertEqual(resp.status_code, 302)
        self.img.refresh_from_db()
        self.assertTrue(self.img.explain)

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

    @patch("Dermal.views.fast_api")
    def test_upload_rate_limited(self, m_fast):
        m_fast.return_value = {"results": [], "heatmap_base64": None}
        statuses = []
        for i in range(11):
            resp = self.client.post("/upload/", {
                "image": "data:image/jpeg;base64," + base64.b64encode(TINY_PNG).decode()
            })
            statuses.append(resp.status_code)
        self.assertIn(429, statuses)  # rate-limit
        self.assertEqual(statuses.count(302), 10)


class PharmacyPageTests(TestCase):
    def test_pharmacy_renders(self):
        resp = self.client.get("/pharmacy/")
        self.assertEqual(resp.status_code, 200)


@override_settings(STORAGES=TEST_STORAGES, MEDIA_ROOT=tempfile.mkdtemp())
class SmokeRenderTests(TestCase):
    """Mọi trang chính phải render 200 (bug P0 cũ: navbar thiếu route -> 500)."""

    def setUp(self):
        self.user, self.profile = make_profile()
        self.client.force_login(self.user)
        self.img = Leaf_image.objects.create(
            image=SimpleUploadedFile("s.png", TINY_PNG, content_type="image/png"),
            user=self.profile, result=[{"class": "Bacterial_spot", "probability": 91.0}],
            explain="<p>Báo cáo</p>",
        )

    def test_all_pages_render(self):
        pages = ["/", "/login/", "/signup/", "/chatbot/", "/profile/",
                 f"/result/{self.img.id}/", "/pharmacy/", "/health/"]
        for url in pages:
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertEqual(resp.status_code, 200, f"{url} -> {resp.status_code}")

    def test_admin_login_page(self):
        resp = self.client.get("/admin/login/")
        self.assertEqual(resp.status_code, 200)

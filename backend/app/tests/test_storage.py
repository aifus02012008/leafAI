"""Image storage backends: local (default) and Supabase Storage (mocked HTTP)."""
import pytest

from app.core.config import settings
from app.services import storage
from app.services.storage import LocalStorage, StorageError, SupabaseStorage


class _Resp:
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_default_backend_is_local(monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "local")
    assert isinstance(storage.get_storage(), LocalStorage)


def test_supabase_backend_requires_credentials(monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "supabase")
    monkeypatch.setattr(settings, "SUPABASE_URL", None)
    with pytest.raises(StorageError):
        storage.get_storage()


def test_local_storage_is_noop_and_deletes(tmp_path, monkeypatch):
    monkeypatch.setattr(type(settings), "storage_dir", property(lambda self: tmp_path))
    f = tmp_path / "originals" / "a.jpg"
    f.parent.mkdir()
    f.write_bytes(b"x")
    s = LocalStorage()
    s.save("originals/a.jpg", f)
    assert s.signed_url("originals/a.jpg") is None
    s.delete("originals/a.jpg")
    assert not f.exists()


def test_local_storage_refuses_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(type(settings), "storage_dir", property(lambda self: tmp_path))
    outside = tmp_path.parent / "keep.txt"
    outside.write_text("keep")
    LocalStorage().delete("../keep.txt")
    assert outside.exists()


def test_supabase_upload_sign_delete(tmp_path, monkeypatch):
    calls = []

    def fake_request(method, url, **kw):
        calls.append((method, url, kw))
        if "/object/sign/" in url:
            return _Resp(200, {"signedURL": "/object/sign/leaf-images/originals/a.jpg?token=t"})
        return _Resp(200)

    monkeypatch.setattr(storage.httpx, "request", fake_request)
    f = tmp_path / "a.jpg"
    f.write_bytes(b"jpegdata")
    s = SupabaseStorage(url="https://proj.supabase.co", key="service", bucket="leaf-images")

    s.save("originals/a.jpg", f)
    method, url, kw = calls[0]
    assert method == "POST"
    assert url == "https://proj.supabase.co/storage/v1/object/leaf-images/originals/a.jpg"
    assert kw["headers"]["Authorization"] == "Bearer service"
    assert kw["headers"]["Content-Type"] == "image/jpeg"
    assert kw["content"] == b"jpegdata"

    signed = s.signed_url("originals/a.jpg")
    assert signed == "https://proj.supabase.co/storage/v1/object/sign/leaf-images/originals/a.jpg?token=t"

    s.delete("originals/a.jpg")
    assert calls[-1][0] == "DELETE"
    assert calls[-1][2]["json"] == {"prefixes": ["originals/a.jpg"]}


def test_supabase_upload_failure_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(storage.httpx, "request", lambda *a, **k: _Resp(500))
    f = tmp_path / "a.jpg"
    f.write_bytes(b"x")
    with pytest.raises(StorageError):
        SupabaseStorage(url="https://p.supabase.co", key="k", bucket="b").save("originals/a.jpg", f)


def test_supabase_rejects_unsafe_keys():
    s = SupabaseStorage(url="https://p.supabase.co", key="k", bucket="b")
    with pytest.raises(StorageError):
        s.signed_url("../secrets.txt")


def test_image_endpoint_redirects_to_signed_url_when_file_not_local(monkeypatch):
    from fastapi.testclient import TestClient
    from app.main import app

    class FakeRemote:
        def signed_url(self, key):
            return f"https://cdn.example/{key}?sig=1"

    monkeypatch.setattr(storage, "get_storage", lambda: FakeRemote())
    with TestClient(app) as c:
        res = c.get("/api/images/originals/notlocal123_orig.jpg", follow_redirects=False)
    assert res.status_code == 307
    assert res.headers["location"] == "https://cdn.example/originals/notlocal123_orig.jpg?sig=1"


def test_generated_vapid_keys_are_usable_by_pywebpush():
    from py_vapid import Vapid
    from app.scripts.generate_vapid_keys import generate

    public, private = generate()
    assert len(public) == 87  # 65-byte uncompressed P-256 point, base64url without padding
    vapid = Vapid.from_string(private)
    assert vapid.private_key is not None

"""Image storage backends.

- LocalStorage (default): files stay in backend/app/storage and are served by /api/images.
- SupabaseStorage: files are also uploaded to a private Supabase Storage bucket, so they
  survive redeploys on ephemeral hosts; /api/images redirects to a short-lived signed URL
  when the local copy is gone.
"""
from __future__ import annotations

import logging
import mimetypes
import re
from pathlib import Path
from typing import Protocol

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

SIGNED_URL_TTL_SECONDS = 300
_SAFE_KEY = re.compile(r"^(originals|results)/[A-Za-z0-9_.-]+$")


class StorageError(RuntimeError):
    pass


class Storage(Protocol):
    def save(self, key: str, local_path: Path) -> None: ...
    def signed_url(self, key: str) -> str | None: ...
    def delete(self, key: str) -> None: ...


def _check_key(key: str) -> str:
    if not _SAFE_KEY.match(key) or ".." in key:
        raise StorageError(f"Unsafe storage key: {key!r}")
    return key


class LocalStorage:
    """Files already live in settings.storage_dir; nothing to upload."""

    def save(self, key: str, local_path: Path) -> None:
        return None

    def signed_url(self, key: str) -> str | None:
        return None

    def delete(self, key: str) -> None:
        root = settings.storage_dir.resolve()
        target = (root / key).resolve()
        if root in target.parents and target.is_file():
            try:
                target.unlink()
            except OSError as exc:
                logger.warning("Could not delete %s: %s", target, exc)


class SupabaseStorage:
    def __init__(self, url: str, key: str, bucket: str):
        self._base = url.rstrip("/") + "/storage/v1"
        self._key = key
        self._bucket = bucket

    def _headers(self, extra: dict | None = None) -> dict:
        return {"Authorization": f"Bearer {self._key}", "apikey": self._key, **(extra or {})}

    def _request(self, method: str, path: str, **kw) -> httpx.Response:
        try:
            res = httpx.request(method, f"{self._base}{path}", timeout=20.0, **kw)
        except httpx.HTTPError as exc:
            raise StorageError(f"Supabase Storage unreachable: {exc}") from exc
        if res.status_code >= 400:
            raise StorageError(f"Supabase Storage {method} {path} failed ({res.status_code})")
        return res

    def save(self, key: str, local_path: Path) -> None:
        key = _check_key(key)
        content_type = mimetypes.guess_type(local_path.name)[0] or "application/octet-stream"
        self._request(
            "POST",
            f"/object/{self._bucket}/{key}",
            headers=self._headers({"Content-Type": content_type, "x-upsert": "true"}),
            content=local_path.read_bytes(),
        )

    def signed_url(self, key: str) -> str | None:
        key = _check_key(key)
        res = self._request(
            "POST",
            f"/object/sign/{self._bucket}/{key}",
            headers=self._headers(),
            json={"expiresIn": SIGNED_URL_TTL_SECONDS},
        )
        signed = (res.json() or {}).get("signedURL")
        return f"{self._base}{signed}" if signed else None

    def delete(self, key: str) -> None:
        key = _check_key(key)
        self._request("DELETE", f"/object/{self._bucket}", headers=self._headers(), json={"prefixes": [key]})


def get_storage() -> Storage:
    backend = (settings.STORAGE_BACKEND or "local").lower()
    if backend == "local":
        return LocalStorage()
    if backend == "supabase":
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            raise StorageError("STORAGE_BACKEND=supabase requires SUPABASE_URL and SUPABASE_SERVICE_KEY.")
        return SupabaseStorage(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY, settings.SUPABASE_BUCKET)
    raise StorageError(f"Unknown STORAGE_BACKEND: {backend!r}")

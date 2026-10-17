# -*- coding: utf-8 -*-
"""
LEAF_AI — Mật khẩu truy cập website (site-wide password gate).

- Mật khẩu lấy từ biến môi trường SITE_PASSWORD (mặc định theo yêu cầu khách hàng).
- So khớp "mềm": bỏ dấu tiếng Việt, bỏ khoảng trắng, không phân biệt hoa/thường
  => "thcs biên sơn 2026@", "THCS Bien Son 2026@", "thcsbienson2026@" đều hợp lệ
  (máy chấm thi có thể không cài bộ gõ tiếng Việt).
- Sau khi đúng mật khẩu, cấp token HMAC có hạn dùng; đổi SITE_PASSWORD thì mọi
  token cũ tự mất hiệu lực (do chữ ký gắn với phiên bản mật khẩu).
"""

import hashlib
import hmac
import os
import re
import time
import unicodedata
from typing import Optional

DEFAULT_SITE_PASSWORD = "thcs biên sơn 2026@"
TOKEN_TTL_SECONDS = 30 * 24 * 3600  # 30 ngày
COOKIE_NAME = "leaf_site_access"


def normalize_password(raw: str) -> str:
    """Chuẩn hóa: NFC -> bỏ dấu -> đ=>d -> chữ thường -> bỏ mọi khoảng trắng."""
    s = unicodedata.normalize("NFD", str(raw or ""))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    s = s.replace("đ", "d").replace("Đ", "D").lower()
    return re.sub(r"\s+", "", s)


def get_site_password() -> str:
    return os.getenv("SITE_PASSWORD") or DEFAULT_SITE_PASSWORD


def is_gate_enabled() -> bool:
    return (os.getenv("SITE_PASSWORD_DISABLED") or "").lower() not in ("1", "true", "yes")


def check_password(candidate: str) -> bool:
    expected = normalize_password(get_site_password())
    given = normalize_password(candidate)
    if not given:
        return False
    return hmac.compare_digest(given.encode("utf-8"), expected.encode("utf-8"))


def _secret() -> bytes:
    return (os.getenv("SECRET_KEY") or "leaf-ai-secure-secret-key-2026").encode("utf-8")


def _password_version() -> str:
    return hashlib.sha256(normalize_password(get_site_password()).encode("utf-8")).hexdigest()[:12]


def _sign(expires_at: int) -> str:
    msg = f"site-access:{expires_at}:{_password_version()}".encode("utf-8")
    return hmac.new(_secret(), msg, hashlib.sha256).hexdigest()


def make_access_token(now: Optional[int] = None) -> tuple:
    """Trả về (token, expires_at)."""
    expires_at = int(now or time.time()) + TOKEN_TTL_SECONDS
    return f"{expires_at}.{_sign(expires_at)}", expires_at


def verify_access_token(token: Optional[str], now: Optional[int] = None) -> bool:
    if not token or "." not in token:
        return False
    exp_str, sig = token.split(".", 1)
    try:
        expires_at = int(exp_str)
    except ValueError:
        return False
    if expires_at < int(now or time.time()):
        return False
    return hmac.compare_digest(sig, _sign(expires_at))

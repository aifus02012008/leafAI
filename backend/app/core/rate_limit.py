"""In-memory sliding-window rate limiting (per process).

Good enough for a single-instance deployment; move to Redis when scaling out.
Memory is bounded: least-recently-used keys are evicted beyond _MAX_TRACKED_KEYS.
"""
from __future__ import annotations

import threading
import time
from collections import OrderedDict, deque

from fastapi import Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.models.user import User

WINDOW_SECONDS = 60.0
_MAX_TRACKED_KEYS = 50_000

_hits: "OrderedDict[str, deque]" = OrderedDict()
_lock = threading.Lock()


def reset_rate_limits() -> None:
    with _lock:
        _hits.clear()


def hit(key: str, limit: int) -> bool:
    """Record a request; return False when `key` exceeded `limit` in the last minute."""
    now = time.monotonic()
    with _lock:
        window = _hits.get(key)
        if window is None:
            window = deque()
            _hits[key] = window
            while len(_hits) > _MAX_TRACKED_KEYS:
                _hits.popitem(last=False)  # evict least recently used key, O(1)
        else:
            _hits.move_to_end(key)
        while window and now - window[0] > WINDOW_SECONDS:
            window.popleft()
        if len(window) >= limit:
            return False
        window.append(now)
        return True


def too_many_requests() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Bạn thao tác quá nhanh, vui lòng thử lại sau ít phút.",
        headers={"Retry-After": str(int(WINDOW_SECONDS))},
    )


def client_ip(request: Request) -> str:
    """Caller IP. Behind a trusted proxy, use the right-most X-Forwarded-For entry:
    that is the address the proxy itself saw; earlier entries are client-controlled."""
    if settings.TRUST_PROXY_HEADERS:
        forwarded = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
        if forwarded:
            return forwarded[-1]
    return request.client.host if request.client else "unknown"


def limited(key: str, limit: int) -> bool:
    """True when the request must be rejected (rate limiting enabled and limit exceeded)."""
    return settings.RATE_LIMIT_ENABLED and not hit(key, limit)


def limit_auth(request: Request) -> None:
    """Throttle login/register attempts per client IP (brute-force protection)."""
    if limited(f"auth:{client_ip(request)}", settings.AUTH_RATE_LIMIT_PER_MINUTE):
        raise too_many_requests()


def limit_login_email(email: str) -> None:
    """Throttle password guesses against one account, whatever IP they come from."""
    if limited(f"login-email:{email.strip().lower()}", settings.LOGIN_PER_EMAIL_PER_MINUTE):
        raise too_many_requests()


def limit_predict(current_user: User = Depends(get_current_user)) -> User:
    """Throttle model inference per user; returns the authenticated user."""
    if limited(f"predict:{current_user.id}", settings.PREDICT_RATE_LIMIT_PER_MINUTE):
        raise too_many_requests()
    return current_user

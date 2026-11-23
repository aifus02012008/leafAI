"""Web Push delivery (VAPID) for pending notifications."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.notification import Notification, PushSubscription

logger = logging.getLogger(__name__)

SENT, FAILED, GONE = "sent", "failed", "gone"
PUSH_TTL_SECONDS = 24 * 3600
MAX_PUSH_AGE = timedelta(hours=24)   # older alerts are stale: shown in-app only, never pushed
BATCH_SIZE = 200


def push_enabled() -> bool:
    return bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY)


def send_push(sub: PushSubscription, payload: dict) -> str:
    """Send one push message. Returns SENT, FAILED or GONE (subscription expired). Never raises."""
    from pywebpush import WebPushException, webpush  # imported lazily: optional at runtime

    try:
        webpush(
            subscription_info={"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
            data=json.dumps(payload, ensure_ascii=False),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_SUBJECT},
            ttl=PUSH_TTL_SECONDS,
            timeout=10,
        )
        return SENT
    except WebPushException as exc:
        code = getattr(exc.response, "status_code", None)
        if code in (404, 410):
            return GONE
        logger.warning("Web push rejected (HTTP %s)", code)
        return FAILED
    except Exception as exc:  # network errors, timeouts, malformed keys
        logger.warning("Web push failed: %s", type(exc).__name__)
        return FAILED


def _payload(n: Notification) -> dict:
    return {"title": n.title, "body": n.body, "link": n.link or "/", "tag": f"leafai-{n.kind}-{n.id}"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _claim(db: Session, notification_id: int) -> bool:
    """Atomically mark a notification as pushed; False if another run already claimed it."""
    claimed = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.pushed_at.is_(None))
        .update({Notification.pushed_at: _utcnow()}, synchronize_session=False)
    )
    db.commit()
    return claimed == 1


def _expire_stale(db: Session) -> None:
    db.query(Notification).filter(
        Notification.pushed_at.is_(None), Notification.created_at < _utcnow() - MAX_PUSH_AGE
    ).update({Notification.pushed_at: _utcnow()}, synchronize_session=False)
    db.commit()


def _push_to_devices(db: Session, n: Notification) -> int:
    sent = 0
    for sub in db.query(PushSubscription).filter(PushSubscription.user_id == n.user_id).all():
        result = send_push(sub, _payload(n))
        if result == SENT:
            sent += 1
        elif result == GONE:
            db.delete(sub)
    db.commit()
    return sent


def deliver_pending(db: Session) -> int:
    """Push recent, not-yet-pushed notifications to their owners' devices. Returns messages sent."""
    if not push_enabled():
        return 0
    _expire_stale(db)
    pending = (
        db.query(Notification)
        .filter(Notification.pushed_at.is_(None))
        .order_by(Notification.id)
        .limit(BATCH_SIZE)
        .all()
    )
    sent = 0
    for n in pending:
        if _claim(db, n.id):
            sent += _push_to_devices(db, n)
    return sent

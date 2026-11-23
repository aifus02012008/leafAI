from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text

from app.db.base import Base

NOTIFICATION_KINDS = ("radar", "followup")


class Notification(Base):
    """In-app notification; `dedupe_key` guarantees each alert is created once per user."""

    __tablename__ = "notifications"
    __table_args__ = (Index("uq_notifications_user_dedupe", "user_id", "dedupe_key", unique=True),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    kind = Column(String(32), nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    link = Column(String(255), nullable=True)
    dedupe_key = Column(String(200), nullable=False)
    read_at = Column(DateTime, nullable=True)
    pushed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)  # naive UTC


class PushSubscription(Base):
    """Browser Web Push subscription (one row per device/browser)."""

    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(String(1000), nullable=False, unique=True)
    p256dh = Column(String(255), nullable=False)
    auth = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)  # naive UTC

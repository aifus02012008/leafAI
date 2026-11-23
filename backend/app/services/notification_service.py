"""Watched farms, in-app notifications, push subscriptions and location privacy."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.dependencies import resolve_crop
from app.core.config import settings
from app.models.diagnosis import DiagnosisHistory
from app.models.notification import Notification, PushSubscription
from app.models.watched_farm import WatchedFarm
from app.schemas.farm import FarmCreate, FarmUpdate, PushSubscriptionIn
from app.services.radar_service import coarsen

NOTIFICATION_PAGE = 50


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Không tìm thấy {what}.")


# ---------- farms ----------

def list_farms(db: Session, user_id: int) -> list[WatchedFarm]:
    return db.query(WatchedFarm).filter(WatchedFarm.user_id == user_id).order_by(WatchedFarm.id).all()


def create_farm(db: Session, user_id: int, payload: FarmCreate) -> WatchedFarm:
    crop_code = resolve_crop(payload.crop_code).code if payload.crop_code else None
    if db.query(WatchedFarm).filter(WatchedFarm.user_id == user_id).count() >= settings.MAX_FARMS_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Mỗi tài khoản theo dõi tối đa {settings.MAX_FARMS_PER_USER} vườn.",
        )
    farm = WatchedFarm(
        user_id=user_id,
        name=payload.name,
        latitude=coarsen(payload.latitude),
        longitude=coarsen(payload.longitude),
        radius_km=payload.radius_km,
        crop_code=crop_code,
        alerts_enabled=True,
    )
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


def _owned_farm(db: Session, user_id: int, farm_id: int) -> WatchedFarm:
    farm = db.query(WatchedFarm).filter(WatchedFarm.id == farm_id, WatchedFarm.user_id == user_id).first()
    if farm is None:
        raise _not_found("vườn")
    return farm


def update_farm(db: Session, user_id: int, farm_id: int, payload: FarmUpdate) -> WatchedFarm:
    farm = _owned_farm(db, user_id, farm_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(farm, field, value.strip() if isinstance(value, str) else value)
    db.commit()
    db.refresh(farm)
    return farm


def delete_farm(db: Session, user_id: int, farm_id: int) -> None:
    db.delete(_owned_farm(db, user_id, farm_id))
    db.commit()


# ---------- notifications ----------

def list_notifications(db: Session, user_id: int) -> tuple[int, list[Notification]]:
    base = db.query(Notification).filter(Notification.user_id == user_id)
    unread = base.filter(Notification.read_at.is_(None)).count()
    items = base.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(NOTIFICATION_PAGE).all()
    return unread, items


def mark_read(db: Session, user_id: int, notification_id: int) -> None:
    n = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()
    if n is None:
        raise _not_found("thông báo")
    if n.read_at is None:
        n.read_at = _now()
        db.commit()


def mark_all_read(db: Session, user_id: int) -> int:
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read_at.is_(None))
        .update({Notification.read_at: _now()}, synchronize_session=False)
    )
    db.commit()
    return count


def create_notification(db: Session, *, user_id: int, kind: str, title: str, body: str,
                        link: str | None, dedupe_key: str) -> Notification | None:
    """Insert unless (user, dedupe_key) already exists; returns None for duplicates."""
    exists = db.query(Notification.id).filter(
        Notification.user_id == user_id, Notification.dedupe_key == dedupe_key
    ).first()
    if exists:
        return None
    n = Notification(user_id=user_id, kind=kind, title=title, body=body, link=link, dedupe_key=dedupe_key)
    db.add(n)
    try:
        db.commit()
    except IntegrityError:  # concurrent job run inserted the same key
        db.rollback()
        return None
    return n


# ---------- push subscriptions ----------

def upsert_subscription(db: Session, user_id: int, payload: PushSubscriptionIn) -> PushSubscription:
    """Register a browser push endpoint for the current user.

    An endpoint identifies one browser. Moving it to another account (e.g. a different user
    logs in on the same phone) is only allowed when the caller proves possession of the
    subscription by sending the same encryption keys.
    """
    sub = db.query(PushSubscription).filter(PushSubscription.endpoint == payload.endpoint).first()
    if sub is None:
        sub = PushSubscription(endpoint=payload.endpoint, user_id=user_id,
                               p256dh=payload.keys.p256dh, auth=payload.keys.auth)
        db.add(sub)
        try:
            db.commit()
        except IntegrityError:  # concurrent registration of the same endpoint
            db.rollback()
            return upsert_subscription(db, user_id, payload)
        db.refresh(sub)
        return sub
    same_keys = sub.p256dh == payload.keys.p256dh and sub.auth == payload.keys.auth
    if sub.user_id != user_id and not same_keys:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Thiết bị này đã được đăng ký.")
    sub.user_id = user_id
    sub.p256dh = payload.keys.p256dh
    sub.auth = payload.keys.auth
    db.commit()
    db.refresh(sub)
    return sub


def remove_subscription(db: Session, user_id: int, endpoint: str) -> int:
    removed = (
        db.query(PushSubscription)
        .filter(PushSubscription.user_id == user_id, PushSubscription.endpoint == endpoint)
        .delete(synchronize_session=False)
    )
    db.commit()
    return removed


# ---------- privacy ----------

def purge_location_data(db: Session, user_id: int) -> tuple[int, int]:
    """Remove every stored location of the user: shared diagnoses and watched farms."""
    cleared = (
        db.query(DiagnosisHistory)
        .filter(DiagnosisHistory.user_id == user_id, DiagnosisHistory.latitude.isnot(None))
        .update(
            {DiagnosisHistory.latitude: None, DiagnosisHistory.longitude: None, DiagnosisHistory.share_to_radar: False},
            synchronize_session=False,
        )
    )
    farms = db.query(WatchedFarm).filter(WatchedFarm.user_id == user_id).delete(synchronize_session=False)
    db.commit()
    return cleared, farms

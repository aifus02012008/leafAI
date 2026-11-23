"""Watched farms, notifications inbox, Web Push subscriptions and location privacy."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.farm import (
    FarmCreate,
    FarmResponse,
    FarmUpdate,
    LocationPurgeResult,
    NotificationList,
    NotificationResponse,
    PushConfig,
    PushSubscriptionIn,
    PushUnsubscribe,
)
from app.services import notification_service as svc
from app.services.push_service import push_enabled

router = APIRouter(prefix="/api", tags=["Farms & Notifications"])


# ---------- farms ----------

@router.get("/farms", response_model=list[FarmResponse])
def list_farms(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.list_farms(db, current_user.id)


@router.post("/farms", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
def create_farm(payload: FarmCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return svc.create_farm(db, current_user.id, payload)


@router.patch("/farms/{farm_id}", response_model=FarmResponse)
def update_farm(farm_id: int, payload: FarmUpdate, current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    return svc.update_farm(db, current_user.id, farm_id, payload)


@router.delete("/farms/{farm_id}")
def delete_farm(farm_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc.delete_farm(db, current_user.id, farm_id)
    return {"message": "Đã xóa vườn.", "id": farm_id}


# ---------- notifications ----------

@router.get("/notifications", response_model=NotificationList)
def list_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    unread, items = svc.list_notifications(db, current_user.id)
    return NotificationList(unread_count=unread, items=[NotificationResponse.model_validate(n) for n in items])


@router.post("/notifications/read-all")
def read_all(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return {"updated": svc.mark_all_read(db, current_user.id)}


@router.post("/notifications/{notification_id}/read")
def read_one(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    svc.mark_read(db, current_user.id, notification_id)
    return {"id": notification_id}


# ---------- push ----------

@router.get("/push/config", response_model=PushConfig)
def push_config():
    enabled = push_enabled()
    return PushConfig(enabled=enabled, public_key=settings.VAPID_PUBLIC_KEY if enabled else None)


@router.post("/push/subscriptions", status_code=status.HTTP_201_CREATED)
def subscribe(payload: PushSubscriptionIn, current_user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    sub = svc.upsert_subscription(db, current_user.id, payload)
    return {"id": sub.id}


@router.delete("/push/subscriptions")
def unsubscribe(payload: PushUnsubscribe, current_user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    return {"removed": svc.remove_subscription(db, current_user.id, payload.endpoint)}


# ---------- privacy ----------

@router.delete("/privacy/location", response_model=LocationPurgeResult)
def purge_location(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Xóa toàn bộ dữ liệu vị trí của người dùng (ca bệnh đã chia sẻ và vườn theo dõi)."""
    cleared, farms = svc.purge_location_data(db, current_user.id)
    return LocationPurgeResult(diagnoses_cleared=cleared, farms_deleted=farms)

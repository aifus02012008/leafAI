from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Only real browser push services may receive server-side POSTs (prevents SSRF via push endpoints).
PUSH_HOSTS = ("fcm.googleapis.com", "updates.push.services.mozilla.com", "web.push.apple.com")
PUSH_HOST_SUFFIXES = (".notify.windows.com", ".push.apple.com", ".push.services.mozilla.com")


class FarmCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_km: float = Field(default=5, gt=0, le=50)
    crop_code: Optional[str] = Field(default=None, max_length=32)

    @field_validator("name")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Tên vườn không được để trống.")
        return v


class FarmUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    radius_km: Optional[float] = Field(default=None, gt=0, le=50)
    alerts_enabled: Optional[bool] = None


class FarmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    latitude: float
    longitude: float
    radius_km: float
    crop_code: Optional[str] = None
    alerts_enabled: bool
    created_at: datetime


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    title: str
    body: str
    link: Optional[str] = None
    read_at: Optional[datetime] = None
    created_at: datetime


class NotificationList(BaseModel):
    unread_count: int
    items: list[NotificationResponse]


class PushKeys(BaseModel):
    p256dh: str = Field(min_length=1, max_length=255)
    auth: str = Field(min_length=1, max_length=255)


def _is_push_service(endpoint: str) -> bool:
    parsed = urlparse(endpoint)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        return False
    return host in PUSH_HOSTS or host.endswith(PUSH_HOST_SUFFIXES)


class PushSubscriptionIn(BaseModel):
    endpoint: str = Field(min_length=10, max_length=1000)
    keys: PushKeys

    @field_validator("endpoint")
    @classmethod
    def _known_push_service(cls, v: str) -> str:
        if not _is_push_service(v):
            raise ValueError("Endpoint không thuộc dịch vụ Web Push được hỗ trợ.")
        return v


class PushUnsubscribe(BaseModel):
    endpoint: str = Field(min_length=10, max_length=1000)


class PushConfig(BaseModel):
    enabled: bool
    public_key: Optional[str] = None


class LocationPurgeResult(BaseModel):
    diagnoses_cleared: int
    farms_deleted: int


class AlertJobReport(BaseModel):
    farms_checked: int
    radar_created: int
    followup_created: int
    pushed: int

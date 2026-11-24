"""Disease library seed data, keyed by crop code, and the idempotent seeding routine."""
from __future__ import annotations

import logging
from types import MappingProxyType

from sqlalchemy.orm import Session

from app.db.seed.durian import DURIAN_DISEASES
from app.db.seed.guava import GUAVA_DISEASES
from app.db.seed.mangosteen import MANGOSTEEN_DISEASES
from app.db.seed.pomelo import POMELO_DISEASES
from app.db.seed.rambutan import RAMBUTAN_DISEASES
from app.db.seed.tea import TEA_DISEASES
from app.models.disease import Disease

logger = logging.getLogger(__name__)

SEED_BY_CROP = MappingProxyType({
    "tea": tuple(TEA_DISEASES),
    "durian": tuple(DURIAN_DISEASES),
    "mangosteen": tuple(MANGOSTEEN_DISEASES),
    "rambutan": tuple(RAMBUTAN_DISEASES),
    "pomelo": tuple(POMELO_DISEASES),
    "guava": tuple(GUAVA_DISEASES),
})

SEED_FIELDS = (
    "display_name",
    "description",
    "symptoms",
    "prevention",
    "treatment",
    "treatment_steps",
    "recovery_info",
)


def _sync_crop(db: Session, crop_code: str, items: tuple[dict, ...]) -> None:
    wanted = {item["class_name"]: item for item in items}
    existing = db.query(Disease).filter(Disease.crop_code == crop_code).all()

    for row in existing:
        if row.class_name not in wanted:
            db.delete(row)  # stale/legacy entry no longer in the catalog

    by_name = {row.class_name: row for row in existing}
    for class_name, item in wanted.items():
        row = by_name.get(class_name)
        if row is None:
            db.add(Disease(crop_code=crop_code, **item))
            continue
        for field in SEED_FIELDS:
            setattr(row, field, item.get(field))


def seed_diseases(db: Session) -> None:
    """Insert or refresh the disease library for every crop. Safe to run on every startup."""
    for crop_code, items in SEED_BY_CROP.items():
        _sync_crop(db, crop_code, items)
    db.commit()
    logger.info(
        "Disease library synced: %s",
        ", ".join(f"{code}={len(items)}" for code, items in SEED_BY_CROP.items()),
    )

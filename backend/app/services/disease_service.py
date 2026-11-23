from __future__ import annotations
from sqlalchemy.orm import Session
from app.models.disease import Disease


def get_all_diseases(db: Session, search: str | None = None, crop_code: str | None = None) -> list[Disease]:
    query = db.query(Disease)
    if crop_code:
        query = query.filter(Disease.crop_code == crop_code)
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            Disease.display_name.ilike(term) |
            Disease.class_name.ilike(term) |
            Disease.description.ilike(term)
        )
    return query.order_by(Disease.id.asc()).all()


def get_disease_by_id(disease_id: int, db: Session) -> Disease | None:
    return db.query(Disease).filter(Disease.id == disease_id).first()


def get_disease_by_class_name(class_name: str, db: Session, crop_code: str = "tea") -> Disease | None:
    return db.query(Disease).filter(
        Disease.crop_code == crop_code,
        Disease.class_name == class_name,
    ).first()

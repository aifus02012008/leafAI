from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from datetime import datetime, timezone
from app.db.base import Base

class Disease(Base):
    __tablename__ = "diseases"
    __table_args__ = (
        Index("uq_diseases_crop_class", "crop_code", "class_name", unique=True),
    )

    id = Column(Integer, primary_key=True, index=True)
    crop_code = Column(String(32), nullable=False, default="tea", server_default="tea", index=True)
    class_name = Column(String(100), nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    symptoms = Column(Text, nullable=True)
    prevention = Column(Text, nullable=True)
    treatment = Column(Text, nullable=True)
    treatment_steps = Column(Text, nullable=True)
    recovery_info = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base

TREATMENT_STATUSES = ("awaiting_followup", "evaluated")


class Treatment(Base):
    """One spray application recorded by the grower after a diagnosis."""

    __tablename__ = "treatments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    diagnosis_id = Column(Integer, ForeignKey("diagnosis_history.id", ondelete="SET NULL"), nullable=True)
    crop_code = Column(String(32), nullable=False, index=True)
    disease_name = Column(String(200), nullable=True)
    active_code = Column(String(64), nullable=False, index=True)
    product_name = Column(String(200), nullable=True)
    applied_on = Column(Date, nullable=False)
    phi_days = Column(Integer, nullable=True)          # pre-harvest interval from the label
    followup_due_on = Column(Date, nullable=False)
    area_m2 = Column(Float, nullable=True)
    total_product = Column(Float, nullable=True)
    estimated_cost = Column(Float, nullable=True)
    severity_before = Column(Float, nullable=True)
    status = Column(String(32), nullable=False, default="awaiting_followup")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    followups = relationship(
        "TreatmentFollowup",
        back_populates="treatment",
        cascade="all, delete-orphan",
        order_by="TreatmentFollowup.created_at",
        lazy="selectin",
    )


class TreatmentFollowup(Base):
    """Re-photo of the treated leaf and the before/after verdict."""

    __tablename__ = "treatment_followups"

    id = Column(Integer, primary_key=True, index=True)
    treatment_id = Column(Integer, ForeignKey("treatments.id", ondelete="CASCADE"), nullable=False, index=True)
    diagnosis_id = Column(Integer, ForeignKey("diagnosis_history.id", ondelete="SET NULL"), nullable=True)
    severity_after = Column(Float, nullable=True)
    relative_change = Column(Float, nullable=True)
    verdict = Column(String(16), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    treatment = relationship("Treatment", back_populates="followups")

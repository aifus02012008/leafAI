from sqlalchemy import Boolean, Column, Integer, String, Float, DateTime, ForeignKey, false
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base

FEEDBACK_VALUES = ("correct", "incorrect", "unsure")

class DiagnosisHistory(Base):
    __tablename__ = "diagnosis_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    crop_code = Column(String(32), nullable=False, default="tea", server_default="tea", index=True)
    model_version = Column(String(64), nullable=True)
    original_image_path = Column(String(500), nullable=False)
    result_image_path = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, default="no_detection")
    inference_time = Column(Float, nullable=True)
    # % diện tích vết bệnh trên diện tích lá (đo bằng xử lý ảnh), dùng so sánh trước/sau điều trị
    severity_pct = Column(Float, nullable=True)
    # Radar dịch bệnh: chỉ lưu vị trí (làm tròn ~110 m) khi người dùng đồng ý chia sẻ
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    share_to_radar = Column(Boolean, nullable=False, default=False, server_default=false())
    # Người dùng xác nhận kết quả: correct | incorrect | unsure (dữ liệu để train lại model)
    user_feedback = Column(String(16), nullable=True)
    feedback_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="diagnoses")
    detections = relationship("DetectionResult", back_populates="diagnosis", cascade="all, delete-orphan", lazy="joined")

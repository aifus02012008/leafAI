from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, computed_field

FeedbackValue = Literal["correct", "incorrect", "unsure"]


class DetectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float


class DiagnosisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    crop_code: str = "tea"
    model_version: Optional[str] = None
    original_image_url: str
    result_image_url: Optional[str] = None
    status: str
    inference_time: Optional[float] = None
    created_at: datetime
    detections: list[DetectionResponse] = []
    user_feedback: Optional[FeedbackValue] = None
    severity_pct: Optional[float] = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def analysis_source(self) -> Literal["model", "gemini"]:
        """"gemini" when the Gemini leaf skill produced this diagnosis (shown as an AI reference)."""
        return "gemini" if (self.model_version or "").startswith("gemini-vision") else "model"


class DiagnosisListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    crop_code: str = "tea"
    original_image_url: str
    result_image_url: Optional[str] = None
    status: str
    inference_time: Optional[float] = None
    created_at: datetime
    detection_count: int = 0
    primary_disease: Optional[str] = None
    max_confidence: Optional[float] = None
    user_feedback: Optional[FeedbackValue] = None


class PredictResponse(DiagnosisResponse):
    summary: str


class FeedbackRequest(BaseModel):
    feedback: FeedbackValue


class FeedbackResponse(BaseModel):
    id: int
    user_feedback: FeedbackValue
    feedback_at: datetime

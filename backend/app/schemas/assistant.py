from typing import Literal, Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    crop: Optional[str] = Field(default=None, max_length=32)
    # Ask about a diagnosis the user just made ("Hỏi bác sĩ AI"): crop, disease and confidence come from it.
    diagnosis_id: Optional[int] = Field(default=None, gt=0)


class RelatedDisease(BaseModel):
    id: int
    crop_code: str
    class_name: str


class AskResponse(BaseModel):
    answer: str
    source: Literal["ai", "library"]
    related: list[RelatedDisease] = []

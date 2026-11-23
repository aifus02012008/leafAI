from typing import Literal, Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=2, max_length=500)
    crop: Optional[str] = Field(default=None, max_length=32)


class RelatedDisease(BaseModel):
    id: int
    crop_code: str
    class_name: str


class AskResponse(BaseModel):
    answer: str
    source: Literal["ai", "library"]
    related: list[RelatedDisease] = []

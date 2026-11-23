from pydantic import BaseModel, ConfigDict
from typing import Optional


class DiseaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    crop_code: str = "tea"
    class_name: str
    display_name: str
    description: Optional[str] = None
    symptoms: Optional[str] = None
    prevention: Optional[str] = None
    treatment: Optional[str] = None
    treatment_steps: Optional[str] = None
    recovery_info: Optional[str] = None
    image_path: Optional[str] = None

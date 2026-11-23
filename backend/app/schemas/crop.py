from typing import Optional

from pydantic import BaseModel, ConfigDict


class CropResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    code: str
    name_vi: str
    name_en: str
    scientific_name: str
    is_available: bool
    model_version: Optional[str] = None
    disease_count: int = 0

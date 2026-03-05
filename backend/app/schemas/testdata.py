from pydantic import BaseModel
from typing import Optional


class GenerateDataRequest(BaseModel):
    data_type: str
    count: int = 10
    options: Optional[dict] = None


class GenerateBusinessDataRequest(BaseModel):
    project_id: Optional[int] = None
    template_id: Optional[int] = None
    template: Optional[dict] = None
    count: int = 10


class MaskDataRequest(BaseModel):
    value: str
    data_type: str


class DataSetCreate(BaseModel):
    project_id: Optional[int] = None
    template_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    data: list[dict]

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class DefectBase(BaseModel):
    title: str
    description: Optional[str] = None
    environment: Optional[str] = None
    version: Optional[str] = None
    module: Optional[str] = None
    severity: str = "normal"
    priority: str = "P2"
    reproduce_rate: Optional[str] = None
    steps_to_reproduce: Optional[str] = None
    actual_result: Optional[str] = None
    expected_result: Optional[str] = None
    tags: Optional[list[str]] = None


class DefectCreate(DefectBase):
    project_id: int
    iteration_id: Optional[int] = None
    assignee_id: Optional[int] = None


class DefectUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    severity: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = None
    module: Optional[str] = None
    steps_to_reproduce: Optional[str] = None
    actual_result: Optional[str] = None
    expected_result: Optional[str] = None


class DefectOut(DefectBase):
    id: int
    project_id: int
    status: str
    reporter_id: int
    assignee_id: Optional[int] = None
    ai_category: Optional[str] = None
    ai_root_cause: Optional[str] = None
    ai_suggestion: Optional[str] = None
    similar_defect_ids: Optional[list[int]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AiAnalyzeDefectRequest(BaseModel):
    defect_id: int
    description: str


class DefectStatusChange(BaseModel):
    status: str
    comment: Optional[str] = None

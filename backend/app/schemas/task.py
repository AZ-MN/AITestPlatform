from datetime import datetime
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.schemas.testcase import GenerateRequest


class TaskCreateGenerate(BaseModel):
    payload: GenerateRequest


class TaskCreateReparse(BaseModel):
    requirement_id: int
    use_ai: bool = True
    ai_provider: Optional[str] = None
    parse_prompt: Optional[str] = None


class TaskOut(BaseModel):
    id: int
    task_type: str
    status: str
    progress: int
    message: Optional[str]
    error: Optional[str]
    params: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    cancel_requested: int
    project_id: Optional[int]
    requirement_id: Optional[int]
    created_by: int
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    queue_position: Optional[int] = None

    class Config:
        from_attributes = True

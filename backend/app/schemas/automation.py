from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class ScriptBase(BaseModel):
    name: str
    description: Optional[str] = None
    script_type: str = "api"
    language: str = "python"
    content: str = ""


class ScriptCreate(ScriptBase):
    project_id: int
    source_case_ids: Optional[list[int]] = None


class ScriptUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None


class ScriptOut(ScriptBase):
    id: int
    project_id: int
    is_ai_generated: bool
    version: int
    creator_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TaskBase(BaseModel):
    name: str
    trigger_type: str = "manual"
    cron_expr: Optional[str] = None
    retry_max: int = 3
    notify_on_fail: bool = True


class TaskCreate(TaskBase):
    project_id: int
    script_id: Optional[int] = None
    target_ids: Optional[list[int]] = None
    task_type: str = "script"


class TaskOut(TaskBase):
    id: int
    project_id: int
    status: str
    next_run_at: Optional[datetime] = None
    creator_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AiGenerateScriptRequest(BaseModel):
    project_id: int
    script_type: str = "api"
    api_definition_id: Optional[int] = None
    case_ids: Optional[list[int]] = None
    url: Optional[str] = None
    steps: Optional[str] = None
    base_url: Optional[str] = "http://localhost:8080"

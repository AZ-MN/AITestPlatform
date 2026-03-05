from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class RequirementBase(BaseModel):
    title: str
    description: Optional[str] = None
    module: Optional[str] = None
    priority: str = "P1"


class RequirementCreate(RequirementBase):
    project_id: int
    iteration_id: Optional[int] = None
    source_type: Optional[str] = "manual"


class RequirementOut(RequirementBase):
    id: int
    project_id: int
    status: str
    parsed_content: Optional[dict] = None
    creator_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TestCaseBase(BaseModel):
    title: str
    module: Optional[str] = None
    sub_module: Optional[str] = None
    preconditions: Optional[str] = None
    steps: Optional[list[dict]] = None
    expected_result: Optional[str] = None
    case_type: str = "functional"
    priority: str = "P1"
    tags: Optional[list[str]] = None


class TestCaseCreate(TestCaseBase):
    project_id: int
    requirement_id: Optional[int] = None
    iteration_id: Optional[int] = None


class TestCaseUpdate(BaseModel):
    title: Optional[str] = None
    module: Optional[str] = None
    preconditions: Optional[str] = None
    steps: Optional[list[dict]] = None
    expected_result: Optional[str] = None
    case_type: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class TestCaseOut(TestCaseBase):
    id: int
    project_id: int
    requirement_id: Optional[int] = None
    status: str = "active"
    is_ai_generated: bool
    creator_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AiGenerateCasesRequest(BaseModel):
    project_id: int
    requirement_id: Optional[int] = None
    content: str
    save_to_db: bool = True

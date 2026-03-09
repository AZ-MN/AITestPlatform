from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime


class RequirementPoint(BaseModel):
    id: str
    title: str
    description: str
    priority: str = "P1"   # P0/P1/P2/P3
    module: str = ""
    conditions: List[str] = []
    rules: List[str] = []


class RequirementCreate(BaseModel):
    project_id: int
    title: str
    content: Optional[str] = None
    source_type: str = "text"  # text / file / api_doc


class RequirementUpdate(BaseModel):
    title: Optional[str] = None
    parse_result: Optional[List[Dict]] = None


class RequirementOut(BaseModel):
    id: int
    project_id: int
    title: str
    content: Optional[str]
    source_type: str
    source_filename: Optional[str]
    status: str
    parse_result: Optional[List[Dict]]
    req_points_count: int
    created_at: datetime
    updated_at: datetime
    creator_name: Optional[str] = None

    class Config:
        from_attributes = True


class RequirementParseRequest(BaseModel):
    requirement_id: int
    confirm_points: Optional[List[Dict]] = None  # 用户确认/编辑后的需求点

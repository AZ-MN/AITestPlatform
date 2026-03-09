from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: str = "📋"


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    status: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    status: str
    icon: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = 0
    case_count: Optional[int] = 0
    req_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ProjectMemberAdd(BaseModel):
    user_id: int
    role: str

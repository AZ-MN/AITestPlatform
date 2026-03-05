from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    env_config: Optional[dict] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    env_config: Optional[dict] = None


class ProjectOut(ProjectBase):
    id: int
    owner_id: Optional[int] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class IterationBase(BaseModel):
    name: str
    version: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None


class IterationCreate(IterationBase):
    project_id: int


class IterationOut(IterationBase):
    id: int
    project_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

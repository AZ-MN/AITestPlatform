from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserOut(UserBase):
    id: int
    is_superuser: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    role_name: Optional[str] = None

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    name: str
    code: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    permission_ids: list[int] = []


class RoleOut(RoleBase):
    id: int
    is_system: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[UserOut] = None


class LoginRequest(BaseModel):
    username: str
    password: str

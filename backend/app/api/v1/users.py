from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.deps import get_db, get_current_user
from app.core.security import get_password_hash
from app.models.user import User, Role
from app.schemas.user import UserCreate, UserUpdate, UserOut, RoleCreate, RoleOut
from typing import Optional

router = APIRouter()


@router.get("/", response_model=list[UserOut])
async def list_users(
    skip: int = 0, limit: int = 20, keyword: Optional[str] = None,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    query = select(User)
    if keyword:
        query = query.where(User.username.contains(keyword) | User.full_name.contains(keyword))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    return [UserOut(id=u.id, username=u.username, full_name=u.full_name, email=u.email,
                    phone=u.phone, role_id=u.role_id, is_active=u.is_active,
                    is_superuser=u.is_superuser, last_login=u.last_login, created_at=u.created_at)
            for u in users]


@router.post("/", response_model=UserOut)
async def create_user(
    data: UserCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=data.username, full_name=data.full_name, email=data.email,
        phone=data.phone, role_id=data.role_id, is_active=data.is_active,
        hashed_password=get_password_hash(data.password),
    )
    db.add(user)
    await db.flush()
    return UserOut(id=user.id, username=user.username, full_name=user.full_name,
                   email=user.email, phone=user.phone, role_id=user.role_id,
                   is_active=user.is_active, is_superuser=user.is_superuser,
                   last_login=user.last_login, created_at=user.created_at)


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int, data: UserUpdate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    return UserOut(id=user.id, username=user.username, full_name=user.full_name,
                   email=user.email, phone=user.phone, role_id=user.role_id,
                   is_active=user.is_active, is_superuser=user.is_superuser,
                   last_login=user.last_login, created_at=user.created_at)


@router.delete("/{user_id}")
async def delete_user(
    user_id: int, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    await db.delete(user)
    return {"message": "删除成功"}


@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: int, new_password: str, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.hashed_password = get_password_hash(new_password)
    return {"message": "密码重置成功"}


# Roles
@router.get("/roles/", response_model=list[RoleOut])
async def list_roles(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Role))
    return result.scalars().all()


@router.post("/roles/", response_model=RoleOut)
async def create_role(data: RoleCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    role = Role(name=data.name, code=data.code, description=data.description)
    db.add(role)
    await db.flush()
    return role

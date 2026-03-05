from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
from app.core.deps import get_db, get_current_user
from app.core.security import verify_password, create_access_token, get_password_hash
from app.models.user import User
from app.schemas.user import LoginRequest, Token, UserOut

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="账户已被禁用")
    # 更新最后登录时间
    await db.execute(update(User).where(User.id == user.id).values(last_login=datetime.utcnow()))
    await db.commit()
    token = create_access_token(subject=user.id)
    user_out = UserOut(
        id=user.id, username=user.username, full_name=user.full_name,
        email=user.email, phone=user.phone, role_id=user.role_id,
        is_active=user.is_active, is_superuser=user.is_superuser,
        last_login=user.last_login, created_at=user.created_at,
    )
    return Token(access_token=token, user=user_out)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id, username=current_user.username,
        full_name=current_user.full_name, email=current_user.email,
        phone=current_user.phone, role_id=current_user.role_id,
        is_active=current_user.is_active, is_superuser=current_user.is_superuser,
        last_login=current_user.last_login, created_at=current_user.created_at,
    )

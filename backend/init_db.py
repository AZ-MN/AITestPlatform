"""初始化数据库并创建默认管理员账号"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings
from app.db.base import Base
from app.core.security import get_password_hash
from app.models import *  # noqa: F401, F403


async def init_db():
    engine = create_async_engine(settings.DATABASE_URL, echo=True)
    
    # 创建所有表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        from app.models.user import User, Role
        
        # 创建默认角色
        roles_data = [
            {"name": "超级管理员", "code": "super_admin", "is_system": True},
            {"name": "系统管理员", "code": "sys_admin", "is_system": True},
            {"name": "项目管理员", "code": "project_admin", "is_system": True},
            {"name": "测试工程师", "code": "tester", "is_system": True},
            {"name": "开发工程师", "code": "developer", "is_system": True},
            {"name": "产品经理", "code": "pm", "is_system": True},
            {"name": "只读用户", "code": "viewer", "is_system": True},
        ]
        
        for role_data in roles_data:
            result = await session.execute(select(Role).where(Role.code == role_data["code"]))
            if not result.scalar_one_or_none():
                role = Role(**role_data)
                session.add(role)
        
        await session.flush()
        
        # 创建默认超级管理员
        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin = User(
                username="admin",
                full_name="超级管理员",
                email="admin@aitest.com",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_superuser=True,
            )
            session.add(admin)
            print("✅ 创建默认管理员账号: admin / admin123")
        
        await session.commit()
        print("✅ 数据库初始化完成")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_db())

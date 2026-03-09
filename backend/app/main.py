from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import settings
from app.core.database import init_db

# Import ALL models before init_db so SQLAlchemy resolves relationships correctly
from app.models.user import User          # noqa: F401
from app.models.project import Project, ProjectMember  # noqa: F401
from app.models.requirement import Requirement         # noqa: F401
from app.models.testcase import TestCase, AIModelConfig  # noqa: F401
from app.models.task_job import TaskJob  # noqa: F401

from app.api import auth, projects, requirements, cases, models as models_api, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化数据库
    init_db()
    _seed_default_data()
    yield


def _seed_default_data():
    """初始化默认管理员账号和示例项目"""
    from app.core.database import SessionLocal
    from app.core.security import get_password_hash

    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            admin = User(
                username="admin",
                email="admin@aitest.com",
                hashed_password=get_password_hash("Admin@123"),
                full_name="超级管理员",
                role="super_admin",
            )
            db.add(admin)
            db.flush()
            # 示例项目
            proj = Project(
                name="电商平台 V2.0",
                description="电商核心业务测试项目，覆盖用户、商品、订单、支付模块",
                icon="🛒",
                created_by=admin.id,
            )
            db.add(proj)
            db.flush()
            db.add(ProjectMember(project_id=proj.id, user_id=admin.id, role="project_admin"))
            db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于大语言模型的测试用例智能生成平台 API",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由注册
app.include_router(auth.router,         prefix="/api/v1")
app.include_router(projects.router,     prefix="/api/v1")
app.include_router(requirements.router, prefix="/api/v1")
app.include_router(cases.router,        prefix="/api/v1")
app.include_router(models_api.router,   prefix="/api/v1")
app.include_router(tasks.router,        prefix="/api/v1")


@app.get("/api/v1/health", tags=["系统"])
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}


# 挂载上传目录（开发用）
if os.path.exists(settings.UPLOAD_DIR):
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

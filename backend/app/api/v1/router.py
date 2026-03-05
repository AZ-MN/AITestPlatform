from fastapi import APIRouter
from app.api.v1 import auth, users, projects, requirements, testcases, apitest, automation, defects, reports, testdata, llm_configs

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(projects.router, prefix="/projects", tags=["项目管理"])
api_router.include_router(requirements.router, prefix="/requirements", tags=["需求管理"])
api_router.include_router(testcases.router, prefix="/testcases", tags=["测试用例"])
api_router.include_router(apitest.router, prefix="/apitest", tags=["接口测试"])
api_router.include_router(automation.router, prefix="/automation", tags=["自动化测试"])
api_router.include_router(defects.router, prefix="/defects", tags=["缺陷管理"])
api_router.include_router(reports.router, prefix="/reports", tags=["质量报告"])
api_router.include_router(testdata.router, prefix="/testdata", tags=["测试数据"])
api_router.include_router(llm_configs.router, prefix="/llm-configs", tags=["LLM配置"])

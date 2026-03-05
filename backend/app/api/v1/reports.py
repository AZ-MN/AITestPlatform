from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.requirement import TestCase
from app.models.defect import Defect
from app.models.automation import TaskExecution
from app.models.apitest import ApiExecution
from app.services.ai_report import generate_test_report
from app.schemas.report import ReportGenerateRequest

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard(
    project_id: int, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取项目质量看板数据"""
    # 用例统计
    case_count = await db.scalar(select(func.count(TestCase.id)).where(TestCase.project_id == project_id))
    case_by_priority = {}
    for priority in ["P0", "P1", "P2", "P3"]:
        cnt = await db.scalar(
            select(func.count(TestCase.id)).where(TestCase.project_id == project_id, TestCase.priority == priority)
        )
        case_by_priority[priority] = cnt or 0

    # 缺陷统计
    defect_count = await db.scalar(select(func.count(Defect.id)).where(Defect.project_id == project_id))
    open_defects = await db.scalar(
        select(func.count(Defect.id)).where(Defect.project_id == project_id, Defect.status.not_in(["closed"]))
    )
    defect_by_severity = {}
    for severity in ["blocker", "critical", "normal", "minor", "trivial"]:
        cnt = await db.scalar(
            select(func.count(Defect.id)).where(Defect.project_id == project_id, Defect.severity == severity)
        )
        defect_by_severity[severity] = cnt or 0

    # 执行统计
    total_exec = await db.scalar(select(func.count(TaskExecution.id)).where(TaskExecution.project_id == project_id))
    passed_exec = await db.scalar(
        select(func.count(TaskExecution.id)).where(TaskExecution.project_id == project_id, TaskExecution.status == "passed")
    )

    pass_rate = round((passed_exec or 0) / (total_exec or 1) * 100, 1)

    return {
        "cases": {"total": case_count or 0, "by_priority": case_by_priority},
        "defects": {"total": defect_count or 0, "open": open_defects or 0, "by_severity": defect_by_severity},
        "executions": {"total": total_exec or 0, "passed": passed_exec or 0, "pass_rate": pass_rate},
    }


@router.post("/ai-report")
async def generate_ai_report(
    data: ReportGenerateRequest, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI 生成测试报告"""
    execution_data = {
        "total_executions": data.total_executions,
        "passed": data.passed,
        "failed": data.failed,
        "pass_rate": f"{round(data.passed / max(data.total_executions, 1) * 100, 1)}%",
    }
    defect_data = {
        "total": data.defect_total,
        "by_severity": data.defect_by_severity,
        "open": data.defect_open,
    }
    report = await generate_test_report(
        project_name=data.project_name,
        iteration_name=data.iteration_name,
        execution_data=execution_data,
        defect_data=defect_data,
    )
    return {"message": "报告生成成功", "report": report}

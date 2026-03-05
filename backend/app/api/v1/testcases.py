from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.requirement import TestCase
from app.schemas.testcase import TestCaseCreate, TestCaseUpdate, TestCaseOut, AiGenerateCasesRequest
from app.services.ai_case_gen import generate_test_cases
from typing import Optional

router = APIRouter()


@router.get("/", response_model=list[TestCaseOut])
async def list_test_cases(
    project_id: int, requirement_id: Optional[int] = None,
    module: Optional[str] = None, priority: Optional[str] = None,
    case_type: Optional[str] = None, skip: int = 0, limit: int = 50,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    query = select(TestCase).where(TestCase.project_id == project_id)
    if requirement_id:
        query = query.where(TestCase.requirement_id == requirement_id)
    if module:
        query = query.where(TestCase.module == module)
    if priority:
        query = query.where(TestCase.priority == priority)
    if case_type:
        query = query.where(TestCase.case_type == case_type)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=TestCaseOut)
async def create_test_case(
    data: TestCaseCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tc = TestCase(**data.model_dump(), creator_id=current_user.id)
    db.add(tc)
    await db.flush()
    return tc


@router.put("/{case_id}", response_model=TestCaseOut)
async def update_test_case(
    case_id: int, data: TestCaseUpdate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(TestCase).where(TestCase.id == case_id))
    tc = result.scalar_one_or_none()
    if not tc:
        raise HTTPException(status_code=404, detail="用例不存在")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(tc, k, v)
    return tc


@router.delete("/{case_id}")
async def delete_test_case(
    case_id: int, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(TestCase).where(TestCase.id == case_id))
    tc = result.scalar_one_or_none()
    if not tc:
        raise HTTPException(status_code=404, detail="用例不存在")
    await db.delete(tc)
    return {"message": "删除成功"}


@router.post("/ai-generate", response_model=list[TestCaseOut])
async def ai_generate_cases(
    data: AiGenerateCasesRequest, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI 生成测试用例"""
    cases_data = await generate_test_cases(data.content)
    created = []
    if data.save_to_db:
        for case_info in cases_data:
            tc = TestCase(
                project_id=data.project_id,
                requirement_id=data.requirement_id,
                title=case_info.get("title", ""),
                module=case_info.get("module", ""),
                case_type=case_info.get("case_type", "functional"),
                priority=case_info.get("priority", "P1"),
                preconditions=case_info.get("preconditions", ""),
                steps=case_info.get("steps", []),
                expected_result=case_info.get("expected_result", ""),
                is_ai_generated=True,
                creator_id=current_user.id,
            )
            db.add(tc)
            created.append(tc)
        await db.flush()
    return created if data.save_to_db else [
        TestCase(id=0, project_id=data.project_id, **{k: v for k, v in c.items() if k in TestCase.__table__.columns.keys()})
        for c in cases_data
    ]

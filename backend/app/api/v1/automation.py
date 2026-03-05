from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.automation import Script, ScheduledTask, TaskExecution
from app.schemas.automation import ScriptCreate, ScriptUpdate, ScriptOut, TaskCreate, TaskOut, AiGenerateScriptRequest
from app.services.ai_script_gen import generate_pytest_script, generate_playwright_script
from app.models.apitest import ApiDefinition, ApiCase
from typing import Optional

router = APIRouter()


@router.get("/scripts", response_model=list[ScriptOut])
async def list_scripts(
    project_id: int, script_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    query = select(Script).where(Script.project_id == project_id)
    if script_type:
        query = query.where(Script.script_type == script_type)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/scripts", response_model=ScriptOut)
async def create_script(
    data: ScriptCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    script = Script(**data.model_dump(), creator_id=current_user.id)
    db.add(script)
    await db.flush()
    return script


@router.put("/scripts/{script_id}", response_model=ScriptOut)
async def update_script(
    script_id: int, data: ScriptUpdate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Script).where(Script.id == script_id))
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="脚本不存在")
    # 保存版本历史
    history = script.history or []
    history.append({"version": script.version, "content": script.content})
    script.history = history
    script.version = script.version + 1
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(script, k, v)
    return script


@router.post("/scripts/ai-generate", response_model=ScriptOut)
async def ai_generate_script(
    data: AiGenerateScriptRequest, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI 生成自动化脚本"""
    if data.script_type == "api" and data.api_definition_id:
        # 获取接口信息
        res = await db.execute(select(ApiDefinition).where(ApiDefinition.id == data.api_definition_id))
        api_def = res.scalar_one_or_none()
        if not api_def:
            raise HTTPException(status_code=404, detail="接口不存在")
        # 获取用例
        cases = []
        if data.case_ids:
            res2 = await db.execute(select(ApiCase).where(ApiCase.id.in_(data.case_ids)))
            cases = [{"name": c.name, "body": c.body, "assertions": c.assertions} for c in res2.scalars().all()]
        result_data = await generate_pytest_script(
            api_name=api_def.name, method=api_def.method,
            base_url=data.base_url, path=api_def.path, cases=cases,
        )
    elif data.script_type == "ui" and data.url:
        result_data = await generate_playwright_script(url=data.url, steps=data.steps or "")
    else:
        raise HTTPException(status_code=400, detail="参数不完整")

    script = Script(
        project_id=data.project_id,
        name=result_data.get("filename", "ai_generated_script.py"),
        content=result_data.get("content", ""),
        script_type=data.script_type,
        is_ai_generated=True,
        creator_id=current_user.id,
    )
    db.add(script)
    await db.flush()
    return script


# Tasks
@router.get("/tasks", response_model=list[TaskOut])
async def list_tasks(project_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ScheduledTask).where(ScheduledTask.project_id == project_id))
    return result.scalars().all()


@router.post("/tasks", response_model=TaskOut)
async def create_task(
    data: TaskCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = ScheduledTask(**data.model_dump(), creator_id=current_user.id)
    db.add(task)
    await db.flush()
    return task

import asyncio
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app.core.security import get_current_user
from app.models.user import User
from app.models.task_job import TaskJob
from app.models.requirement import Requirement
from app.models.testcase import TestCase, AIModelConfig
from app.schemas.task import TaskOut, TaskCreateGenerate, TaskCreateReparse
from app.services.ai_service import (
    AIAdapter, SYSTEM_PROMPT_CASE_GEN, SYSTEM_PROMPT_API_CASE,
    SYSTEM_PROMPT_REQ_PARSE, build_case_gen_prompt, parse_ai_json_response
)
from app.services.document_parser import extract_requirement_points_with_rules

router = APIRouter(prefix="/tasks", tags=["任务中心"])

_WORKER_RUNNING = False


def _resolve_model_config(db: Session, provider: Optional[str]):
    q = db.query(AIModelConfig).filter(AIModelConfig.is_active == 1)
    if provider:
        return q.filter(AIModelConfig.provider == provider).order_by(AIModelConfig.is_default.desc(), AIModelConfig.id.desc()).first()
    return q.order_by(AIModelConfig.is_default.desc(), AIModelConfig.id.desc()).first()


def _task_to_dict(t: TaskJob) -> dict:
    d = {c.name: getattr(t, c.name) for c in t.__table__.columns}
    return d


def _touch_worker():
    global _WORKER_RUNNING
    if not _WORKER_RUNNING:
        _WORKER_RUNNING = True
        asyncio.create_task(_worker_loop())


async def _worker_loop():
    global _WORKER_RUNNING
    while True:
        db = SessionLocal()
        try:
            task = db.query(TaskJob).filter(TaskJob.status == "queued").order_by(TaskJob.created_at.asc()).first()
            if not task:
                _WORKER_RUNNING = False
                return
            if task.cancel_requested:
                task.status = "stopped"
                task.progress = 100
                task.message = "任务已停止"
                task.finished_at = datetime.utcnow()
                db.commit()
                continue
            task.status = "running"
            task.started_at = datetime.utcnow()
            task.progress = 10
            task.message = "任务执行中"
            db.commit()

            try:
                if task.task_type == "generate_cases":
                    await _run_generate_task(db, task)
                elif task.task_type == "reparse_requirement":
                    await _run_reparse_task(db, task)
                else:
                    raise RuntimeError(f"未知任务类型: {task.task_type}")

                if task.cancel_requested:
                    task.status = "stopped"
                    task.message = "任务已停止"
                else:
                    task.status = "success"
                    task.message = "任务完成"
                task.progress = 100
                task.finished_at = datetime.utcnow()
                db.commit()
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                task.message = "任务失败"
                task.finished_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
        await asyncio.sleep(0.2)


async def _run_reparse_task(db: Session, task: TaskJob):
    p = task.params or {}
    req = db.query(Requirement).filter(Requirement.id == p.get("requirement_id")).first()
    if not req:
        raise RuntimeError("需求不存在")
    content = req.content or ""
    use_ai = bool(p.get("use_ai", True))
    ai_provider = p.get("ai_provider")
    parse_prompt = p.get("parse_prompt") or ""

    task.progress = 40
    task.message = "解析需求点"
    db.commit()

    if use_ai and content.strip():
        cfg = _resolve_model_config(db, ai_provider)
        provider = ai_provider or (cfg.provider if cfg else None)
        adapter = AIAdapter(
            provider=provider,
            api_key=cfg.api_key if cfg else None,
            api_base_url=cfg.api_base_url if cfg else None,
            model=cfg.model_name if cfg else None,
            temperature=float(cfg.temperature) if cfg and cfg.temperature else 0.3,
        )
        prompt = "请将以下需求文档按最小可测试行为进行细粒度拆分：\n\n"
        if parse_prompt.strip():
            prompt += f"补充解析提示词：{parse_prompt.strip()}\n\n"
        raw = await adapter.chat(SYSTEM_PROMPT_REQ_PARSE, f"{prompt}{content[:15000]}")
        parsed = parse_ai_json_response(raw)
        if not parsed:
            parsed = extract_requirement_points_with_rules(content)
    else:
        parsed = extract_requirement_points_with_rules(content)

    req.parse_result = parsed
    req.req_points_count = len(parsed)
    req.status = "parsed"
    task.requirement_id = req.id
    task.project_id = req.project_id
    task.result = {"requirement_id": req.id, "points": len(parsed)}
    db.commit()


async def _run_generate_task(db: Session, task: TaskJob):
    p = task.params or {}
    req_points = p.get("req_points") or []
    requirement_id = p.get("requirement_id")
    if not req_points and requirement_id:
        req = db.query(Requirement).filter(Requirement.id == requirement_id).first()
        if req and req.parse_result:
            req_points = req.parse_result
    if not req_points:
        raise RuntimeError("未找到需求点")

    module_filter = p.get("module_filter")
    priority_filter = p.get("priority_filter")
    if module_filter:
        req_points = [x for x in req_points if module_filter in (x.get("module") or "")]
    if priority_filter:
        req_points = [x for x in req_points if x.get("priority") == priority_filter]
    if not req_points:
        raise RuntimeError("过滤后无可生成需求点")

    task.progress = 35
    task.message = "调用AI生成用例"
    db.commit()

    test_type = p.get("test_type") or "functional"
    system_prompt = SYSTEM_PROMPT_API_CASE if test_type == "api" else SYSTEM_PROMPT_CASE_GEN
    user_msg = build_case_gen_prompt(
        req_points=req_points,
        test_type=test_type,
        granularity=p.get("granularity") or "medium",
        cover_scenarios=p.get("cover_scenarios") or ["normal", "exception", "boundary"],
        custom_instructions=p.get("custom_instructions") or "",
    )
    cfg = _resolve_model_config(db, p.get("ai_provider"))
    provider = p.get("ai_provider") or (cfg.provider if cfg else None)
    adapter = AIAdapter(
        provider=provider,
        api_key=cfg.api_key if cfg else None,
        api_base_url=cfg.api_base_url if cfg else None,
        model=cfg.model_name if cfg else None,
        temperature=p.get("temperature", 0.3),
    )
    raw_response = await adapter.chat(system_prompt, user_msg, max_tokens=8192)
    ai_cases = parse_ai_json_response(raw_response)
    if not ai_cases:
        raise RuntimeError("AI未返回有效用例")

    task.progress = 70
    task.message = "保存用例"
    db.commit()

    batch_id = str(uuid.uuid4())[:8]
    created_by = task.created_by
    saved_count = 0
    for idx, c in enumerate(ai_cases, 1):
        case_obj = TestCase(
            project_id=p.get("project_id"),
            requirement_id=requirement_id,
            created_by=created_by,
            case_id=f"TC-{batch_id}-{idx:03d}",
            module=c.get("module", ""),
            title=c.get("title", f"用例{idx}"),
            case_level=c.get("case_level", "P1"),
            test_type=c.get("test_type", test_type),
            stage=c.get("stage", "system"),
            preconditions=c.get("preconditions", ""),
            steps=c.get("steps", []),
            expected_results=[s.get("expected", "") for s in c.get("steps", [])],
            remarks=c.get("remarks", ""),
            ai_generated=1,
            generation_batch=batch_id,
            status="draft",
        )
        db.add(case_obj)
        saved_count += 1
    db.commit()
    task.result = {"batch_id": batch_id, "total": saved_count}
    task.project_id = p.get("project_id")
    task.requirement_id = requirement_id
    db.commit()


@router.get("", summary="获取任务列表")
async def list_tasks(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(TaskJob).order_by(TaskJob.created_at.desc())
    if current_user.role != "super_admin":
        q = q.filter(TaskJob.created_by == current_user.id)
    if project_id:
        q = q.filter(TaskJob.project_id == project_id)
    if status:
        q = q.filter(TaskJob.status == status)
    tasks = q.limit(200).all()
    queued_ids = [x.id for x in db.query(TaskJob).filter(TaskJob.status == "queued").order_by(TaskJob.created_at.asc()).all()]
    position_map = {tid: i + 1 for i, tid in enumerate(queued_ids)}
    result = []
    for t in tasks:
        item = _task_to_dict(t)
        if t.status == "queued":
            item["queue_position"] = position_map.get(t.id)
        result.append(item)
    return result


@router.post("/generate", response_model=TaskOut, summary="创建用例生成任务")
async def create_generate_task(
    req: TaskCreateGenerate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = TaskJob(
        task_type="generate_cases",
        status="queued",
        progress=0,
        message="排队中",
        params=req.payload.model_dump(),
        project_id=req.payload.project_id,
        requirement_id=req.payload.requirement_id,
        created_by=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    _touch_worker()
    return _task_to_dict(task)


@router.post("/reparse", response_model=TaskOut, summary="创建需求重新解析任务")
async def create_reparse_task(
    req: TaskCreateReparse,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    requirement = db.query(Requirement).filter(Requirement.id == req.requirement_id).first()
    if not requirement:
        raise HTTPException(status_code=404, detail="需求不存在")
    task = TaskJob(
        task_type="reparse_requirement",
        status="queued",
        progress=0,
        message="排队中",
        params=req.model_dump(),
        project_id=requirement.project_id,
        requirement_id=req.requirement_id,
        created_by=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    _touch_worker()
    return _task_to_dict(task)


@router.post("/{task_id}/stop", summary="停止任务")
async def stop_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(TaskJob).filter(TaskJob.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    if current_user.role != "super_admin" and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权限")
    task.cancel_requested = 1
    if task.status == "queued":
        task.status = "stopped"
        task.progress = 100
        task.message = "任务已停止"
        task.finished_at = datetime.utcnow()
    db.commit()
    return {"message": "停止请求已提交"}


@router.post("/{task_id}/retry", response_model=TaskOut, summary="重试任务")
async def retry_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    old = db.query(TaskJob).filter(TaskJob.id == task_id).first()
    if not old:
        raise HTTPException(status_code=404, detail="任务不存在")
    if old.status not in ("failed", "stopped"):
        raise HTTPException(status_code=400, detail="仅失败或已停止任务可重试")
    task = TaskJob(
        task_type=old.task_type,
        status="queued",
        progress=0,
        message="排队中",
        params=old.params,
        project_id=old.project_id,
        requirement_id=old.requirement_id,
        created_by=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    _touch_worker()
    return _task_to_dict(task)

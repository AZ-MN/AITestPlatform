import uuid
import time
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.testcase import TestCase, CaseReviewLog
from app.models.requirement import Requirement
from app.schemas.testcase import (
    TestCaseCreate, TestCaseUpdate, TestCaseOut,
    GenerateRequest, GenerateResponse, TestCaseRating, ExportRequest
)
from app.services.ai_service import (
    AIAdapter, SYSTEM_PROMPT_CASE_GEN, SYSTEM_PROMPT_API_CASE,
    build_case_gen_prompt, parse_ai_json_response
)
from app.services.export_service import export_cases

router = APIRouter(prefix="/cases", tags=["测试用例"])


def _case_to_dict(case: TestCase, db: Session) -> dict:
    d = {c.name: getattr(case, c.name) for c in case.__table__.columns}
    creator = db.query(User).filter(User.id == case.created_by).first()
    d["creator_name"] = creator.full_name if creator else ""
    return d


def _review_to_dict(log: CaseReviewLog, db: Session) -> dict:
    creator = db.query(User).filter(User.id == log.created_by).first()
    return {
        "id": log.id,
        "case_id": log.case_id,
        "action": log.action,
        "from_status": log.from_status,
        "to_status": log.to_status,
        "comment": log.comment,
        "detail": log.detail,
        "created_by": log.created_by,
        "created_by_name": creator.full_name if creator else "",
        "created_at": log.created_at,
    }


def _log_case_action(
    db: Session,
    case_id: int,
    user_id: int,
    action: str,
    from_status: Optional[str] = None,
    to_status: Optional[str] = None,
    comment: Optional[str] = None,
    detail: Optional[dict] = None,
):
    db.add(CaseReviewLog(
        case_id=case_id,
        action=action,
        from_status=from_status,
        to_status=to_status,
        comment=comment,
        detail=detail or {},
        created_by=user_id,
    ))


def _build_fallback_cases(req_points: List[dict], test_type: str, cover_scenarios: List[str], granularity: str) -> List[dict]:
    scenario_label_map = {
        "normal": "正常流程",
        "exception": "异常场景",
        "boundary": "边界场景",
        "permission": "权限控制",
        "compatibility": "兼容性",
        "security": "安全性",
    }
    scenario_pool = [s for s in cover_scenarios if s in scenario_label_map] or ["normal", "exception", "boundary"]
    keep_count = {"coarse": 1, "medium": 2, "fine": len(scenario_pool)}.get(granularity, 2)
    selected_scenarios = scenario_pool[:keep_count]
    stage = "integration" if test_type == "api" else ("system" if test_type == "functional" else "unit")

    cases: List[dict] = []
    for rp in req_points:
        module = rp.get("module", "通用模块")
        title = rp.get("title") or "需求验证"
        priority = rp.get("priority", "P1")
        for s in selected_scenarios:
            scenario_cn = scenario_label_map.get(s, s)
            cases.append({
                "module": module,
                "title": f"{title} - {scenario_cn}",
                "case_level": priority,
                "test_type": test_type,
                "stage": stage,
                "preconditions": f"已进入{module}，并具备执行“{title}”的基础环境",
                "steps": [
                    {"step": 1, "action": f"准备{scenario_cn}输入数据并发起操作", "expected": "系统接收请求且无异常崩溃"},
                    {"step": 2, "action": "观察界面提示、返回结果与状态变化", "expected": f"结果符合{scenario_cn}预期且满足需求描述"},
                ],
                "remarks": "规则引擎兜底生成（未使用外部模型）",
            })
    return cases


def _validate_case_status(status: str) -> str:
    allowed = {"draft", "pending_review", "reviewed", "deprecated"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"不支持的状态：{status}")
    return status


# ── 列表与查询 ─────────────────────────────────────────────────

@router.get("", summary="获取用例列表")
async def list_cases(
    project_id: int,
    requirement_id: Optional[int] = None,
    module: Optional[str] = None,
    test_type: Optional[str] = None,
    case_level: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    generation_batch: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(TestCase).filter(TestCase.project_id == project_id)
    if requirement_id:
        q = q.filter(TestCase.requirement_id == requirement_id)
    if module:
        q = q.filter(TestCase.module.contains(module))
    if test_type:
        q = q.filter(TestCase.test_type == test_type)
    if case_level:
        q = q.filter(TestCase.case_level == case_level)
    if status:
        q = q.filter(TestCase.status == status)
    if generation_batch:
        q = q.filter(TestCase.generation_batch == generation_batch)
    if keyword:
        q = q.filter(
            TestCase.title.contains(keyword) |
            TestCase.preconditions.contains(keyword)
        )
    total = q.count()
    cases = q.order_by(TestCase.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_case_to_dict(c, db) for c in cases]
    }


# ── AI 智能生成 ───────────────────────────────────────────────

@router.post("/generate", summary="AI 智能生成测试用例")
async def generate_cases(
    gen_req: GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    batch_id = str(uuid.uuid4())[:8]

    # 获取需求点
    req_points = gen_req.req_points or []
    if not req_points and gen_req.requirement_id:
        req = db.query(Requirement).filter(Requirement.id == gen_req.requirement_id).first()
        if req and req.parse_result:
            req_points = req.parse_result

    if not req_points:
        raise HTTPException(status_code=400, detail="未找到需求点，请先解析需求或直接传入需求点")

    # 按模块过滤
    if gen_req.module_filter:
        req_points = [p for p in req_points if gen_req.module_filter in p.get("module", "")]

    # 按优先级过滤
    if gen_req.priority_filter:
        req_points = [p for p in req_points if p.get("priority") == gen_req.priority_filter]

    if not req_points:
        raise HTTPException(status_code=400, detail="过滤后没有符合条件的需求点")

    # 选择对应 Prompt
    system_prompt = SYSTEM_PROMPT_API_CASE if gen_req.test_type == "api" else SYSTEM_PROMPT_CASE_GEN
    user_msg = build_case_gen_prompt(
        req_points=req_points,
        test_type=gen_req.test_type,
        granularity=gen_req.granularity,
        cover_scenarios=gen_req.cover_scenarios,
        custom_instructions=gen_req.custom_instructions or "",
    )

    generation_mode = "ai"
    ai_cases: List[dict] = []

    # 调用 AI（失败时自动降级到规则生成，确保平台可用）
    adapter = AIAdapter(provider=gen_req.ai_provider, temperature=gen_req.temperature)
    try:
        raw_response = await adapter.chat(system_prompt, user_msg, max_tokens=8192)
        ai_cases = parse_ai_json_response(raw_response)
    except Exception:
        ai_cases = []

    if not ai_cases:
        generation_mode = "rule"
        ai_cases = _build_fallback_cases(
            req_points=req_points,
            test_type=gen_req.test_type,
            cover_scenarios=gen_req.cover_scenarios,
            granularity=gen_req.granularity,
        )

    if not ai_cases:
        raise HTTPException(status_code=500, detail="未生成到有效用例，请检查需求点后重试")

    # 持久化到数据库
    saved = []
    for idx, c in enumerate(ai_cases, 1):
        case_obj = TestCase(
            project_id=gen_req.project_id,
            requirement_id=gen_req.requirement_id,
            created_by=current_user.id,
            case_id=f"TC-{batch_id}-{idx:03d}",
            module=c.get("module", ""),
            title=c.get("title", f"用例{idx}"),
            case_level=c.get("case_level", "P1"),
            test_type=c.get("test_type", gen_req.test_type),
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
        saved.append(case_obj)

    db.commit()
    for c in saved:
        db.refresh(c)

    elapsed = round(time.time() - start_time, 2)
    return {
        "batch_id": batch_id,
        "total": len(saved),
        "cases": [_case_to_dict(c, db) for c in saved],
        "elapsed_seconds": elapsed,
        "generation_mode": generation_mode,
    }


# ── 统计（必须在 /{case_id} 之前注册，避免路由冲突）─────────────

@router.get("/stats/summary", summary="项目用例统计")
async def case_stats(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from sqlalchemy import func
    total = db.query(TestCase).filter(TestCase.project_id == project_id).count()
    by_level = db.query(TestCase.case_level, func.count()).filter(
        TestCase.project_id == project_id
    ).group_by(TestCase.case_level).all()
    by_type = db.query(TestCase.test_type, func.count()).filter(
        TestCase.project_id == project_id
    ).group_by(TestCase.test_type).all()
    by_status = db.query(TestCase.status, func.count()).filter(
        TestCase.project_id == project_id
    ).group_by(TestCase.status).all()
    ai_count = db.query(TestCase).filter(
        TestCase.project_id == project_id, TestCase.ai_generated == 1
    ).count()
    return {
        "total_cases": total,
        "ai_generated": ai_count,
        "manual": total - ai_count,
        "by_level": dict(by_level),
        "by_type": dict(by_type),
        "by_status": dict(by_status),
    }


@router.get("/regression/minimal", summary="生成最小回归用例集")
async def minimal_regression_cases(
    project_id: int,
    changed_modules: Optional[str] = None,
    limit: int = Query(30, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(TestCase).filter(TestCase.project_id == project_id)
    q = q.filter(TestCase.status.in_(["reviewed", "pending_review", "draft"]))
    module_list = [m.strip() for m in (changed_modules or "").split(",") if m.strip()]
    if module_list:
        from sqlalchemy import or_
        q = q.filter(or_(*[TestCase.module.contains(m) for m in module_list]))

    cases = q.order_by(TestCase.updated_at.desc()).limit(500).all()

    def _score(c: TestCase):
        level_weight = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(c.case_level or "P3", 3)
        status_weight = {"reviewed": 0, "pending_review": 1, "draft": 2}.get(c.status or "draft", 3)
        return (level_weight, status_weight, -(c.id or 0))

    picked = sorted(cases, key=_score)[:limit]
    return {"total": len(picked), "items": [_case_to_dict(c, db) for c in picked]}


# ── 单条 CRUD ─────────────────────────────────────────────────

@router.patch("/status/batch", summary="批量更新用例状态")
async def batch_update_case_status(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    case_ids = payload.get("case_ids") or []
    status = _validate_case_status(payload.get("status", ""))
    if not isinstance(case_ids, list) or not case_ids:
        raise HTTPException(status_code=400, detail="case_ids 不能为空")
    target_cases = db.query(TestCase).filter(TestCase.id.in_(case_ids)).all()
    for c in target_cases:
        old_status = c.status
        c.status = status
        _log_case_action(
            db=db,
            case_id=c.id,
            user_id=current_user.id,
            action="status_change",
            from_status=old_status,
            to_status=status,
            comment=f"批量更新状态为 {status}",
        )
    db.commit()
    return {"message": f"已更新 {len(case_ids)} 条用例状态", "status": status}

@router.get("/{case_id}", summary="获取用例详情")
async def get_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    return _case_to_dict(case, db)


@router.get("/{case_id}/reviews", summary="获取用例评审记录")
async def list_case_reviews(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    logs = db.query(CaseReviewLog).filter(CaseReviewLog.case_id == case_id).order_by(CaseReviewLog.created_at.desc()).all()
    return [_review_to_dict(log, db) for log in logs]


@router.post("", summary="手动创建用例")
async def create_case(
    case_in: TestCaseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    count = db.query(TestCase).filter(TestCase.project_id == case_in.project_id).count()
    case = TestCase(
        **case_in.model_dump(),
        created_by=current_user.id,
        case_id=f"TC-{count + 1:04d}",
        ai_generated=0,
        status="draft",
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return _case_to_dict(case, db)


@router.put("/{case_id}", summary="更新用例")
async def update_case(
    case_id: int,
    case_in: TestCaseUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    update_payload = case_in.model_dump(exclude_unset=True)
    old_status = case.status
    for field, value in update_payload.items():
        setattr(case, field, value)
    _log_case_action(
        db=db,
        case_id=case.id,
        user_id=current_user.id,
        action="update",
        from_status=old_status,
        to_status=case.status,
        comment="更新用例内容",
        detail={"fields": list(update_payload.keys())},
    )
    db.commit()
    db.refresh(case)
    return _case_to_dict(case, db)


@router.patch("/{case_id}/status", summary="更新用例状态")
async def update_case_status(
    case_id: int,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    old_status = case.status
    new_status = _validate_case_status(payload.get("status", ""))
    case.status = new_status
    _log_case_action(
        db=db,
        case_id=case.id,
        user_id=current_user.id,
        action="status_change",
        from_status=old_status,
        to_status=new_status,
        comment=f"状态变更为 {new_status}",
    )
    db.commit()
    db.refresh(case)
    return _case_to_dict(case, db)


@router.delete("/{case_id}", summary="删除用例")
async def delete_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    db.delete(case)
    db.commit()
    return {"message": "删除成功"}


@router.delete("", summary="批量删除用例")
async def batch_delete_cases(
    case_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    db.query(TestCase).filter(TestCase.id.in_(case_ids)).delete(synchronize_session=False)
    db.commit()
    return {"message": f"已删除 {len(case_ids)} 条用例"}


@router.post("/{case_id}/rating", summary="对用例评分反馈")
async def rate_case(
    case_id: int,
    rating_in: TestCaseRating,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    case = db.query(TestCase).filter(TestCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    case.rating = rating_in.rating
    case.feedback = rating_in.feedback
    _log_case_action(
        db=db,
        case_id=case.id,
        user_id=current_user.id,
        action="rating",
        from_status=case.status,
        to_status=case.status,
        comment=f"评分 {rating_in.rating} 星",
        detail={"rating": rating_in.rating, "feedback": rating_in.feedback or ""},
    )
    db.commit()
    return {"message": "评分提交成功"}


# ── 导出 ──────────────────────────────────────────────────────

@router.post("/export", summary="导出用例")
async def export(
    export_req: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(TestCase).filter(TestCase.project_id == export_req.project_id)
    if export_req.case_ids:
        q = q.filter(TestCase.id.in_(export_req.case_ids))
    if export_req.requirement_id:
        q = q.filter(TestCase.requirement_id == export_req.requirement_id)
    cases = q.order_by(TestCase.case_level, TestCase.id).all()
    if not cases:
        raise HTTPException(status_code=404, detail="没有可导出的用例")

    file_bytes, media_type, filename = export_cases(cases, export_req.format)
    return StreamingResponse(
        iter([file_bytes]),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )



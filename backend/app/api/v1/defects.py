from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.defect import Defect, DefectComment
from app.schemas.defect import DefectCreate, DefectUpdate, DefectOut, AiAnalyzeDefectRequest, DefectStatusChange
from app.services.ai_defect import analyze_defect, find_similar_defects
from typing import Optional
from datetime import datetime

router = APIRouter()


@router.get("/", response_model=list[DefectOut])
async def list_defects(
    project_id: int, status: Optional[str] = None, severity: Optional[str] = None,
    assignee_id: Optional[int] = None, keyword: Optional[str] = None,
    skip: int = 0, limit: int = 20,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    query = select(Defect).where(Defect.project_id == project_id)
    if status:
        query = query.where(Defect.status == status)
    if severity:
        query = query.where(Defect.severity == severity)
    if assignee_id:
        query = query.where(Defect.assignee_id == assignee_id)
    if keyword:
        query = query.where(Defect.title.contains(keyword))
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/", response_model=DefectOut)
async def create_defect(
    data: DefectCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    defect = Defect(**data.model_dump(), reporter_id=current_user.id)
    db.add(defect)
    await db.flush()
    return defect


@router.get("/{defect_id}", response_model=DefectOut)
async def get_defect(defect_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    defect = result.scalar_one_or_none()
    if not defect:
        raise HTTPException(status_code=404, detail="缺陷不存在")
    return defect


@router.put("/{defect_id}", response_model=DefectOut)
async def update_defect(
    defect_id: int, data: DefectUpdate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    defect = result.scalar_one_or_none()
    if not defect:
        raise HTTPException(status_code=404, detail="缺陷不存在")
    for k, v in data.model_dump(exclude_none=True).items():
        setattr(defect, k, v)
    return defect


@router.post("/{defect_id}/status")
async def change_defect_status(
    defect_id: int, data: DefectStatusChange, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Defect).where(Defect.id == defect_id))
    defect = result.scalar_one_or_none()
    if not defect:
        raise HTTPException(status_code=404, detail="缺陷不存在")
    defect.status = data.status
    if data.status == "confirmed":
        defect.confirmed_at = datetime.utcnow()
    elif data.status == "closed":
        defect.closed_at = datetime.utcnow()
    elif data.status == "fixing":
        defect.fixed_at = None
    if data.comment:
        comment = DefectComment(
            defect_id=defect_id, content=data.comment,
            user_id=current_user.id, action="status_change",
            extra_data={"new_status": data.status},
        )
        db.add(comment)
    return {"message": f"状态已更新为: {data.status}"}


@router.post("/ai-analyze")
async def ai_analyze_defect(
    data: AiAnalyzeDefectRequest, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI 分析缺陷"""
    analysis = await analyze_defect(data.description)

    # 更新到数据库
    if data.defect_id:
        result = await db.execute(select(Defect).where(Defect.id == data.defect_id))
        defect = result.scalar_one_or_none()
        if defect:
            defect.ai_category = analysis.get("category")
            defect.ai_root_cause = analysis.get("root_cause_analysis")
            defect.ai_suggestion = analysis.get("fix_suggestion")
            defect.ai_structured = analysis.get("structured")

    return {"message": "AI分析完成", "result": analysis}

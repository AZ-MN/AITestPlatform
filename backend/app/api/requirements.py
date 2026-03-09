import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user
from app.models.user import User
from app.models.requirement import Requirement
from app.models.testcase import AIModelConfig
from app.schemas.requirement import RequirementCreate, RequirementUpdate, RequirementOut, RequirementParseRequest
from app.services.document_parser import extract_text_from_file
from app.services.ai_service import AIAdapter, SYSTEM_PROMPT_REQ_PARSE, parse_ai_json_response
from app.services.document_parser import extract_requirement_points_with_rules

router = APIRouter(prefix="/requirements", tags=["需求管理"])


@router.get("", summary="获取需求列表")
async def list_requirements(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reqs = (
        db.query(Requirement)
        .filter(Requirement.project_id == project_id)
        .order_by(Requirement.created_at.desc())
        .all()
    )
    result = []
    for r in reqs:
        item = RequirementOut.model_validate(r).model_dump()
        creator = db.query(User).filter(User.id == r.created_by).first()
        item["creator_name"] = creator.full_name if creator else ""
        result.append(item)
    return result


@router.post("/upload", summary="上传需求文档并解析")
async def upload_requirement(
    project_id: int = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    use_ai: bool = Form(True),
    ai_provider: Optional[str] = Form(None),
    parse_prompt: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 校验文件类型
    ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}")

    # 保存文件
    file_id = str(uuid.uuid4())
    save_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}_{file.filename}")
    async with aiofiles.open(save_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # 创建需求记录（先标记为 parsing）
    req = Requirement(
        project_id=project_id,
        created_by=current_user.id,
        title=title,
        source_type="file",
        source_file=save_path,
        source_filename=file.filename,
        status="parsing",
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    # 提取文本
    try:
        text_content = await extract_text_from_file(save_path, file.filename)
        req.content = text_content[:50000]  # 限制存储长度
    except Exception as e:
        req.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"文档解析失败: {str(e)}")

    # 解析需求点
    parse_result = await _parse_req_points(text_content, use_ai, ai_provider, parse_prompt, db)
    req.parse_result = parse_result
    req.req_points_count = len(parse_result)
    req.status = "parsed"
    db.commit()
    db.refresh(req)

    return RequirementOut.model_validate(req)


@router.post("/text", summary="手动输入需求文本")
async def create_text_requirement(
    req_in: RequirementCreate,
    use_ai: bool = True,
    ai_provider: Optional[str] = None,
    parse_prompt: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = Requirement(
        project_id=req_in.project_id,
        created_by=current_user.id,
        title=req_in.title,
        content=req_in.content,
        source_type="text",
        status="parsing",
    )
    db.add(req)
    db.commit()

    parse_result = await _parse_req_points(req_in.content or "", use_ai, ai_provider, parse_prompt, db)
    req.parse_result = parse_result
    req.req_points_count = len(parse_result)
    req.status = "parsed"
    db.commit()
    db.refresh(req)
    return RequirementOut.model_validate(req)


@router.get("/{req_id}", summary="获取需求详情")
async def get_requirement(
    req_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="需求不存在")
    return RequirementOut.model_validate(req)


@router.put("/{req_id}", summary="更新需求（含确认需求点）")
async def update_requirement(
    req_id: int,
    update_in: RequirementUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="需求不存在")
    for field, value in update_in.model_dump(exclude_unset=True).items():
        setattr(req, field, value)
    if update_in.parse_result is not None:
        req.req_points_count = len(update_in.parse_result)
    db.commit()
    db.refresh(req)
    return RequirementOut.model_validate(req)


@router.delete("/{req_id}", summary="删除需求")
async def delete_requirement(
    req_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="需求不存在")
    db.delete(req)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{req_id}/reparse", summary="重新解析需求点")
async def reparse_requirement(
    req_id: int,
    use_ai: bool = True,
    ai_provider: Optional[str] = None,
    parse_prompt: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="需求不存在")
    if not (req.content and req.content.strip()):
        raise HTTPException(status_code=400, detail="当前需求缺少原始内容，无法重新解析")

    req.status = "parsing"
    db.commit()
    parse_result = await _parse_req_points(req.content, use_ai, ai_provider, parse_prompt, db)
    req.parse_result = parse_result
    req.req_points_count = len(parse_result)
    req.status = "parsed"
    db.commit()
    db.refresh(req)
    return RequirementOut.model_validate(req)


def _resolve_model_config(db: Session, provider: Optional[str]):
    q = db.query(AIModelConfig).filter(AIModelConfig.is_active == 1)
    if provider:
        return q.filter(AIModelConfig.provider == provider).order_by(AIModelConfig.is_default.desc(), AIModelConfig.id.desc()).first()
    return q.order_by(AIModelConfig.is_default.desc(), AIModelConfig.id.desc()).first()


async def _parse_req_points(content: str, use_ai: bool, ai_provider: Optional[str], parse_prompt: Optional[str], db: Session) -> list:
    """内部：解析需求点（AI 优先，失败降级到规则）"""
    if use_ai and content.strip():
        try:
            cfg = _resolve_model_config(db, ai_provider)
            provider = ai_provider or (cfg.provider if cfg else None)
            temperature = float(cfg.temperature) if cfg and cfg.temperature else 0.3
            adapter = AIAdapter(
                provider=provider,
                api_key=cfg.api_key if cfg else None,
                api_base_url=cfg.api_base_url if cfg else None,
                model=cfg.model_name if cfg else None,
                temperature=temperature,
            )
            base_prompt = (
                "请将以下需求文档按最小可测试行为进行细粒度拆分，"
                "优先提取可直接用于测试用例设计的需求点：\n\n"
            )
            if parse_prompt and parse_prompt.strip():
                base_prompt = f"{base_prompt}\n补充解析提示词：{parse_prompt.strip()}\n\n"
            raw = await adapter.chat(SYSTEM_PROMPT_REQ_PARSE, f"{base_prompt}{content[:15000]}")
            parsed = parse_ai_json_response(raw)
            if parsed:
                return parsed
        except Exception:
            pass
    # 降级：规则解析
    return extract_requirement_points_with_rules(content)

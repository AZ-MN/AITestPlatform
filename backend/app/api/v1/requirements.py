from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.requirement import Requirement
from app.schemas.testcase import RequirementCreate, RequirementOut, TestCaseCreate, TestCaseOut
from app.services.ai_case_gen import parse_requirement
from typing import Optional
import aiofiles
import os

router = APIRouter()


@router.get("/", response_model=list[RequirementOut])
async def list_requirements(
    project_id: int, skip: int = 0, limit: int = 20,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Requirement).where(Requirement.project_id == project_id).offset(skip).limit(limit)
    )
    return result.scalars().all()


@router.post("/", response_model=RequirementOut)
async def create_requirement(
    data: RequirementCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    req = Requirement(**data.model_dump(), creator_id=current_user.id)
    db.add(req)
    await db.flush()
    return req


@router.get("/{req_id}", response_model=RequirementOut)
async def get_requirement(req_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Requirement).where(Requirement.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="需求不存在")
    return req


@router.post("/{req_id}/ai-parse")
async def ai_parse_requirement(
    req_id: int, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI 解析需求文档"""
    result = await db.execute(select(Requirement).where(Requirement.id == req_id))
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="需求不存在")
    content = req.description or req.title
    parsed = await parse_requirement(content)
    req.parsed_content = parsed
    req.status = "parsed"
    return {"message": "解析完成", "result": parsed}


@router.post("/upload")
async def upload_requirement_file(
    project_id: int, file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """上传需求文件 (txt/md/docx/pdf)"""
    allowed = [".txt", ".md", ".docx", ".pdf"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式，仅支持: {', '.join(allowed)}")

    upload_dir = "./uploads/requirements"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = f"{upload_dir}/{file.filename}"
    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # 读取文本内容
    text_content = ""
    if ext in [".txt", ".md"]:
        text_content = content.decode("utf-8", errors="ignore")
    elif ext == ".docx":
        try:
            from docx import Document
            import io
            doc = Document(io.BytesIO(content))
            text_content = "\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            text_content = f"文件解析失败: {e}"
    elif ext == ".pdf":
        try:
            import PyPDF2, io
            reader = PyPDF2.PdfReader(io.BytesIO(content))
            text_content = "\n".join([page.extract_text() or "" for page in reader.pages])
        except Exception as e:
            text_content = f"PDF解析失败: {e}"

    req = Requirement(
        project_id=project_id, title=file.filename,
        description=text_content, source_file=file_path,
        source_type=ext.lstrip("."), creator_id=current_user.id,
    )
    db.add(req)
    await db.flush()
    return {"message": "上传成功", "requirement_id": req.id, "content_preview": text_content[:500]}

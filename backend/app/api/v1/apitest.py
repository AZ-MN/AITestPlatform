from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import time
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.apitest import ApiDefinition, ApiCase, ApiExecution
from app.schemas.apitest import (
    ApiDefinitionCreate, ApiDefinitionOut, ApiCaseCreate, ApiCaseOut,
    ApiDebugRequest, ApiDebugResponse, SwaggerImportRequest, AiGenerateApiCasesRequest
)
from app.services.ai_api_gen import generate_api_cases, parse_swagger
from typing import Optional

router = APIRouter()


# API Definitions
@router.get("/definitions", response_model=list[ApiDefinitionOut])
async def list_api_definitions(
    project_id: int, module: Optional[str] = None, skip: int = 0, limit: int = 50,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    query = select(ApiDefinition).where(ApiDefinition.project_id == project_id)
    if module:
        query = query.where(ApiDefinition.module == module)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/definitions", response_model=ApiDefinitionOut)
async def create_api_definition(
    data: ApiDefinitionCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    api = ApiDefinition(**data.model_dump(), creator_id=current_user.id)
    db.add(api)
    await db.flush()
    return api


@router.delete("/definitions/{api_id}")
async def delete_api_definition(
    api_id: int, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(ApiDefinition).where(ApiDefinition.id == api_id))
    api = result.scalar_one_or_none()
    if not api:
        raise HTTPException(status_code=404, detail="接口不存在")
    await db.delete(api)
    return {"message": "删除成功"}


@router.post("/import/swagger", response_model=dict)
async def import_swagger(
    data: SwaggerImportRequest, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导入 Swagger/OpenAPI 文档"""
    apis = await parse_swagger(data.swagger_content)
    created_count = 0
    for api_info in apis:
        api = ApiDefinition(
            project_id=data.project_id,
            name=api_info["name"], method=api_info["method"],
            path=api_info["path"], description=api_info.get("description", ""),
            module=api_info.get("module", "默认"),
            query_params=api_info.get("query_params", {}),
            body_schema=api_info.get("body_schema", {}),
            response_schema=api_info.get("response_schema", {}),
            source="swagger", creator_id=current_user.id,
        )
        db.add(api)
        created_count += 1
    await db.flush()
    return {"message": f"成功导入 {created_count} 个接口"}


# API Cases
@router.get("/cases", response_model=list[ApiCaseOut])
async def list_api_cases(
    project_id: int, api_definition_id: Optional[int] = None,
    skip: int = 0, limit: int = 50,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    query = select(ApiCase).where(ApiCase.project_id == project_id)
    if api_definition_id:
        query = query.where(ApiCase.api_definition_id == api_definition_id)
    result = await db.execute(query.offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/cases", response_model=ApiCaseOut)
async def create_api_case(
    data: ApiCaseCreate, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = ApiCase(**data.model_dump(), creator_id=current_user.id)
    db.add(case)
    await db.flush()
    return case


@router.post("/cases/ai-generate", response_model=list[ApiCaseOut])
async def ai_generate_api_cases(
    data: AiGenerateApiCasesRequest, db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI 生成 API 测试用例"""
    result = await db.execute(select(ApiDefinition).where(ApiDefinition.id == data.api_definition_id))
    api_def = result.scalar_one_or_none()
    if not api_def:
        raise HTTPException(status_code=404, detail="接口定义不存在")

    api_info = {
        "name": api_def.name, "method": api_def.method, "path": api_def.path,
        "description": api_def.description, "query_params": api_def.query_params or {},
        "body_schema": api_def.body_schema or {}, "response_schema": api_def.response_schema or {},
    }
    cases_data = await generate_api_cases(api_info)
    created = []
    if data.save_to_db:
        for case_info in cases_data:
            case = ApiCase(
                project_id=data.project_id,
                api_definition_id=data.api_definition_id,
                name=case_info.get("name", ""),
                description=case_info.get("description", ""),
                body=case_info.get("body", {}),
                query_params=case_info.get("query_params", {}),
                assertions=case_info.get("assertions", []),
                case_type=case_info.get("case_type", "normal"),
                is_ai_generated=True,
                creator_id=current_user.id,
            )
            db.add(case)
            created.append(case)
        await db.flush()
    return created


# API Debug
@router.post("/debug", response_model=ApiDebugResponse)
async def debug_api(data: ApiDebugRequest, current_user: User = Depends(get_current_user)):
    """接口在线调试"""
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=data.timeout) as client:
            response = await client.request(
                method=data.method,
                url=data.url,
                headers=data.headers or {},
                params=data.params or {},
                json=data.body if data.method in ["POST", "PUT", "PATCH"] else None,
            )
        duration = (time.time() - start) * 1000
        try:
            body = response.json()
        except Exception:
            body = response.text
        return ApiDebugResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            body=body,
            response_time_ms=round(duration, 2),
            size_bytes=len(response.content),
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="请求超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"请求失败: {str(e)}")

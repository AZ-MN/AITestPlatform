from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.deps import get_db, get_current_user
from app.models.user import User
from app.models.llm import LLMConfig
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class LLMConfigCreate(BaseModel):
    name: str
    provider: str
    api_key: str
    endpoint: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: int = 4096
    timeout: int = 60
    temperature: float = 0.7
    is_default: bool = False


class LLMConfigOut(BaseModel):
    id: int
    name: str
    provider: str
    endpoint: Optional[str] = None
    model_name: Optional[str] = None
    max_tokens: int
    timeout: int
    is_default: bool
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/", response_model=list[LLMConfigOut])
async def list_llm_configs(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(LLMConfig))
    return result.scalars().all()


@router.post("/", response_model=LLMConfigOut)
async def create_llm_config(data: LLMConfigCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if data.is_default:
        # 取消其他默认
        result = await db.execute(select(LLMConfig).where(LLMConfig.is_default == True))
        for cfg in result.scalars().all():
            cfg.is_default = False
    config = LLMConfig(**data.model_dump())
    db.add(config)
    await db.flush()
    return config


@router.post("/{config_id}/test")
async def test_llm_connection(config_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """测试 LLM 连接"""
    result = await db.execute(select(LLMConfig).where(LLMConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    from app.services.llm_client import LLMClient
    client = LLMClient(api_key=config.api_key, base_url=config.endpoint, model=config.model_name)
    try:
        response = await client.chat([{"role": "user", "content": "Hello, reply with 'OK' only."}], max_tokens=10)
        return {"status": "success", "response": response}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.delete("/{config_id}")
async def delete_llm_config(config_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(LLMConfig).where(LLMConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    await db.delete(config)
    return {"message": "删除成功"}

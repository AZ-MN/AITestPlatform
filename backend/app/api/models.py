from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.testcase import AIModelConfig
from app.schemas.testcase import AIModelConfigCreate, AIModelConfigOut

router = APIRouter(prefix="/models", tags=["AI模型管理"])

SUPPORTED_PROVIDERS = [
    {"id": "openai",    "name": "OpenAI",    "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]},
    {"id": "anthropic", "name": "Anthropic (Claude)", "models": ["claude-opus-4-6", "claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]},
    {"id": "tongyi",    "name": "通义千问",  "models": ["qwen-max", "qwen-plus", "qwen-turbo"]},
    {"id": "zhipu",     "name": "智谱 GLM",  "models": ["glm-4", "glm-4-flash", "glm-3-turbo"]},
    {"id": "deepseek",  "name": "DeepSeek",  "models": ["deepseek-chat", "deepseek-coder"]},
]


@router.get("/providers", summary="获取支持的供应商列表")
async def list_providers():
    return SUPPORTED_PROVIDERS


@router.get("", response_model=List[AIModelConfigOut], summary="获取已配置的模型列表")
async def list_model_configs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(AIModelConfig).filter(AIModelConfig.is_active == 1).all()


@router.post("", response_model=AIModelConfigOut, summary="添加模型配置")
async def add_model_config(
    config_in: AIModelConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role not in ("super_admin", "project_admin"):
        raise HTTPException(status_code=403, detail="权限不足，仅管理员可配置模型")
    # 如果设为默认，清除其他默认
    if config_in.is_default:
        db.query(AIModelConfig).update({"is_default": 0})
    cfg = AIModelConfig(**config_in.model_dump())
    db.add(cfg)
    db.commit()
    db.refresh(cfg)
    return cfg


@router.put("/{config_id}", response_model=AIModelConfigOut, summary="更新模型配置")
async def update_model_config(
    config_id: int,
    config_in: AIModelConfigCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cfg = db.query(AIModelConfig).filter(AIModelConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="配置不存在")
    if config_in.is_default:
        db.query(AIModelConfig).filter(AIModelConfig.id != config_id).update({"is_default": 0})
    for field, value in config_in.model_dump(exclude_unset=True).items():
        setattr(cfg, field, value)
    db.commit()
    db.refresh(cfg)
    return cfg


@router.delete("/{config_id}", summary="删除模型配置")
async def delete_model_config(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cfg = db.query(AIModelConfig).filter(AIModelConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="配置不存在")
    cfg.is_active = 0
    db.commit()
    return {"message": "已删除"}


@router.post("/{config_id}/test", summary="测试模型连通性")
async def test_model(
    config_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cfg = db.query(AIModelConfig).filter(AIModelConfig.id == config_id).first()
    if not cfg:
        raise HTTPException(status_code=404, detail="配置不存在")
    from app.services.ai_service import AIAdapter, AIServiceError
    try:
        adapter = AIAdapter(
            provider=cfg.provider,
            api_key=cfg.api_key,
            api_base_url=cfg.api_base_url,
            model=cfg.model_name,
            temperature=float(cfg.temperature),
        )
        reply = await adapter.chat("你是助手", "请回复：连通性测试成功", max_tokens=50)
        return {"ok": True, "reply": reply}
    except AIServiceError as e:
        return {"ok": False, "error": str(e)}

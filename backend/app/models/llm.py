from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON, Float, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base, TimestampMixin


class LLMConfig(Base, TimestampMixin):
    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="配置名称")
    provider = Column(String(50), nullable=False, comment="openai/qianwen/wenxin/xunfei/custom")
    api_key = Column(String(500), nullable=False, comment="API密钥（加密存储）")
    endpoint = Column(String(500), comment="API端点URL")
    model_name = Column(String(100), comment="模型版本")
    max_tokens = Column(Integer, default=4096)
    timeout = Column(Integer, default=60, comment="超时时间(秒)")
    max_concurrency = Column(Integer, default=5, comment="最大并发数")
    temperature = Column(Float, default=0.7)
    is_default = Column(Boolean, default=False, comment="是否为默认配置")
    is_active = Column(Boolean, default=True)
    extra_config = Column(JSON, comment="额外配置项")


class LLMCallLog(Base):
    __tablename__ = "llm_call_logs"

    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("llm_configs.id"), nullable=True)
    provider = Column(String(50))
    model = Column(String(100))
    module = Column(String(50), comment="调用来源模块: case_gen/api_gen/script_gen/defect/report")
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    duration_ms = Column(Integer, comment="耗时(ms)")
    status = Column(String(20), comment="success/error/timeout")
    error_message = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    request_summary = Column(Text, comment="请求摘要")
    created_at = Column(DateTime, default=datetime.utcnow)

    config = relationship("LLMConfig")

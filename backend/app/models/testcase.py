from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # 用例标准字段
    case_id = Column(String(50))            # 业务用例ID，如 TC-001
    module = Column(String(100))            # 所属模块
    title = Column(String(500), nullable=False)
    case_level = Column(String(10), default="P1")  # P0/P1/P2/P3
    test_type = Column(String(30))          # functional / api / unit / regression
    stage = Column(String(30))              # smoke / integration / system / regression
    preconditions = Column(Text)            # 前置条件
    steps = Column(JSON)                    # 操作步骤列表
    expected_results = Column(JSON)         # 预期结果列表
    remarks = Column(Text)                  # 备注

    # 状态与来源
    status = Column(String(20), default="draft")  # draft / pending_review / reviewed / deprecated
    ai_generated = Column(Integer, default=1)      # 1=AI生成 0=手动创建
    generation_batch = Column(String(50))          # 批次ID

    # 执行信息
    exec_status = Column(String(20))       # passed / failed / blocked / skipped
    exec_result = Column(Text)             # 实际结果
    exec_by = Column(Integer, ForeignKey("users.id"))
    exec_at = Column(DateTime)

    # 评分与反馈
    rating = Column(Integer)               # 1-5 用户评分
    feedback = Column(Text)                # 用户反馈

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="test_cases")
    requirement = relationship("Requirement", back_populates="test_cases")
    creator = relationship("User", back_populates="test_cases", foreign_keys=[created_by])


class AIModelConfig(Base):
    __tablename__ = "ai_model_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))                          # 配置展示名称
    provider = Column(String(30), nullable=False)   # openai / anthropic / tongyi / zhipu / deepseek
    model_name = Column(String(100), nullable=False)
    api_key = Column(String(500))
    api_base_url = Column(String(500))
    temperature = Column(String(10), default="0.3")
    max_tokens = Column(Integer, default=4096)
    is_default = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

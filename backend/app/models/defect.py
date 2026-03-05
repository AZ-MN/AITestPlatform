from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


class Defect(Base, TimestampMixin):
    __tablename__ = "defects"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    iteration_id = Column(Integer, ForeignKey("iterations.id"), nullable=True)
    title = Column(String(500), nullable=False, comment="缺陷标题")
    description = Column(Text, comment="缺陷描述（原始自然语言）")
    environment = Column(String(50), comment="发现环境: dev/test/staging")
    version = Column(String(50), comment="版本号")
    module = Column(String(100), comment="所属模块")
    severity = Column(String(20), default="normal", comment="blocker/critical/normal/minor/trivial")
    priority = Column(String(5), default="P2", comment="P0/P1/P2/P3")
    reproduce_rate = Column(String(20), comment="必现/偶现/难以复现")
    steps_to_reproduce = Column(Text, comment="复现步骤")
    actual_result = Column(Text, comment="实际结果")
    expected_result = Column(Text, comment="预期结果")
    attachments = Column(JSON, comment="附件列表: [{name, url, type}]")
    status = Column(String(20), default="new", comment="new/confirmed/fixing/pending_verify/closed/reopened")
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tags = Column(JSON)
    # AI 分析结果
    ai_category = Column(String(50), comment="AI分类: functional/ui/performance/security/compatibility/logic")
    ai_root_cause = Column(Text, comment="AI根因分析")
    ai_suggestion = Column(Text, comment="AI修复建议")
    ai_structured = Column(JSON, comment="AI结构化结果")
    similar_defect_ids = Column(JSON, comment="相似缺陷ID列表")
    # 外部系统关联
    jira_key = Column(String(50), nullable=True, comment="Jira Issue Key")
    zentao_id = Column(Integer, nullable=True, comment="禅道缺陷ID")
    # 时间节点
    confirmed_at = Column(DateTime, nullable=True)
    fixed_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    project = relationship("Project")
    assignee = relationship("User", foreign_keys=[assignee_id])
    reporter = relationship("User", foreign_keys=[reporter_id])
    comments = relationship("DefectComment", back_populates="defect")


class DefectComment(Base, TimestampMixin):
    __tablename__ = "defect_comments"

    id = Column(Integer, primary_key=True, index=True)
    defect_id = Column(Integer, ForeignKey("defects.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50), comment="comment/status_change/assign")
    extra_data = Column(JSON)

    defect = relationship("Defect", back_populates="comments")
    user = relationship("User")

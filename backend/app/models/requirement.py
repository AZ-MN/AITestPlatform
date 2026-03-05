from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
import enum
from app.db.base import Base, TimestampMixin


class RequirementStatus(str, enum.Enum):
    draft = "draft"
    parsed = "parsed"
    reviewing = "reviewing"
    approved = "approved"


class Requirement(Base, TimestampMixin):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    iteration_id = Column(Integer, ForeignKey("iterations.id"), nullable=True)
    title = Column(String(200), nullable=False, comment="需求标题")
    description = Column(Text, comment="需求描述")
    module = Column(String(100), comment="所属模块")
    priority = Column(String(10), default="P1", comment="P0/P1/P2/P3")
    status = Column(String(20), default="draft")
    source_file = Column(String(500), comment="原始文件路径")
    source_type = Column(String(20), comment="txt/md/docx/pdf/url")
    parsed_content = Column(JSON, comment="AI解析结果: {功能点, 业务规则, 测试点}")
    creator_id = Column(Integer, ForeignKey("users.id"))

    project = relationship("Project")
    creator = relationship("User")
    test_cases = relationship("TestCase", back_populates="requirement")


class TestCaseType(str, enum.Enum):
    functional = "功能"
    exception = "异常"
    boundary = "边界"
    performance = "性能"
    security = "安全"


class TestCase(Base, TimestampMixin):
    __tablename__ = "test_cases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=True)
    iteration_id = Column(Integer, ForeignKey("iterations.id"), nullable=True)
    module = Column(String(100), comment="所属模块")
    sub_module = Column(String(100))
    title = Column(String(500), nullable=False, comment="用例标题")
    preconditions = Column(Text, comment="前置条件")
    steps = Column(JSON, comment="测试步骤列表 [{step, expected}]")
    expected_result = Column(Text, comment="预期结果")
    case_type = Column(String(20), default="functional", comment="功能/异常/边界/性能/安全")
    priority = Column(String(5), default="P1", comment="P0/P1/P2/P3")
    status = Column(String(20), default="active", comment="active/deprecated")
    is_ai_generated = Column(Boolean, default=False)
    tags = Column(JSON, comment="标签列表")
    creator_id = Column(Integer, ForeignKey("users.id"))
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    project = relationship("Project")
    requirement = relationship("Requirement", back_populates="test_cases")
    creator = relationship("User", foreign_keys=[creator_id])


class TestCaseReview(Base, TimestampMixin):
    __tablename__ = "test_case_reviews"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    title = Column(String(200), nullable=False, comment="评审单标题")
    reviewer_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="pending", comment="pending/in_progress/completed")
    case_ids = Column(JSON, comment="评审的用例ID列表")
    comments = Column(JSON, comment="评审意见列表")
    conclusion = Column(String(20), comment="passed/rejected/revised")

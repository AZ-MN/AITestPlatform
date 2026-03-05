from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


class TestDataTemplate(Base, TimestampMixin):
    __tablename__ = "test_data_templates"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(Text)
    category = Column(String(50), comment="user/order/product/payment/custom")
    fields = Column(JSON, nullable=False, comment="字段定义列表 [{name, type, rule, options}]")
    is_system = Column(Boolean, default=False, comment="是否系统内置模板")
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)


class TestDataSet(Base, TimestampMixin):
    __tablename__ = "test_data_sets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    template_id = Column(Integer, ForeignKey("test_data_templates.id"), nullable=True)
    name = Column(String(100), nullable=False, comment="数据集名称")
    description = Column(Text)
    data = Column(JSON, nullable=False, comment="数据内容列表")
    count = Column(Integer, default=0, comment="数据条数")
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    template = relationship("TestDataTemplate")

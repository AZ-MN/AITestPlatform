from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text)               # 原始文档内容
    source_type = Column(String(20))    # file / text / url / api_doc
    source_file = Column(String(500))   # 上传的文件路径
    source_filename = Column(String(200))
    status = Column(String(20), default="parsed")  # uploading / parsing / parsed / failed
    parse_result = Column(JSON)          # 解析后的结构化需求点列表
    req_points_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="requirements")
    creator = relationship("User", back_populates="requirements")
    test_cases = relationship("TestCase", back_populates="requirement")

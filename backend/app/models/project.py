from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="项目名称")
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="active", comment="active/archived")
    env_config = Column(JSON, comment="环境配置 {dev/test/prod: {base_url, headers}}")

    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("ProjectMember", back_populates="project")
    iterations = relationship("Iteration", back_populates="project")


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default="member", comment="admin/member/viewer")

    project = relationship("Project", back_populates="members")
    user = relationship("User")


class Iteration(Base, TimestampMixin):
    __tablename__ = "iterations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False, comment="迭代名称")
    version = Column(String(50), comment="版本号")
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="planning", comment="planning/active/completed")
    description = Column(Text)

    project = relationship("Project", back_populates="iterations")

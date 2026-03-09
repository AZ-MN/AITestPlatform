from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class TaskJob(Base):
    __tablename__ = "task_jobs"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(50), nullable=False)  # generate_cases / reparse_requirement
    status = Column(String(20), default="queued")   # queued/running/success/failed/stopped
    progress = Column(Integer, default=0)
    message = Column(String(255), default="")
    error = Column(Text)
    params = Column(JSON)
    result = Column(JSON)
    cancel_requested = Column(Integer, default=0)

    project_id = Column(Integer, ForeignKey("projects.id"))
    requirement_id = Column(Integer, ForeignKey("requirements.id"))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)

    project = relationship("Project")
    requirement = relationship("Requirement")
    creator = relationship("User")

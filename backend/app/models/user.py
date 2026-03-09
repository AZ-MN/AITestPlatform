from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    PROJECT_ADMIN = "project_admin"
    TEST_LEAD = "test_lead"
    TEST_ENGINEER = "test_engineer"
    PRODUCT_MANAGER = "product_manager"
    DEV_ENGINEER = "dev_engineer"
    VISITOR = "visitor"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(100))
    role = Column(String(30), default=UserRole.TEST_ENGINEER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    avatar = Column(String(500))

    # Relationships
    projects = relationship("ProjectMember", back_populates="user")
    requirements = relationship("Requirement", back_populates="creator", foreign_keys="[Requirement.created_by]")
    test_cases = relationship("TestCase", back_populates="creator", foreign_keys="[TestCase.created_by]")

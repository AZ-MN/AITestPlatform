from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


class Script(Base, TimestampMixin):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False, comment="脚本名称")
    description = Column(Text)
    script_type = Column(String(20), default="api", comment="api/ui")
    language = Column(String(20), default="python", comment="python/javascript")
    content = Column(Text, nullable=False, comment="脚本内容")
    is_ai_generated = Column(Boolean, default=False)
    source_case_ids = Column(JSON, comment="来源用例ID列表")
    creator_id = Column(Integer, ForeignKey("users.id"))
    version = Column(Integer, default=1, comment="版本号")
    history = Column(JSON, comment="历史版本列表 [{version, content, updated_at}]")

    project = relationship("Project")
    executions = relationship("TaskExecution", back_populates="script")


class ScheduledTask(Base, TimestampMixin):
    __tablename__ = "scheduled_tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False, comment="任务名称")
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=True)
    task_type = Column(String(20), default="script", comment="script/api_batch/scenario")
    target_ids = Column(JSON, comment="执行目标ID列表")
    trigger_type = Column(String(20), default="manual", comment="manual/cron/once")
    cron_expr = Column(String(100), nullable=True, comment="Cron表达式")
    next_run_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    retry_max = Column(Integer, default=3)
    notify_on_fail = Column(Boolean, default=True)
    notify_channels = Column(JSON, comment="通知渠道列表")
    status = Column(String(20), default="active", comment="active/disabled")
    creator_id = Column(Integer, ForeignKey("users.id"))

    project = relationship("Project")
    executions = relationship("TaskExecution", back_populates="task")


class TaskExecution(Base, TimestampMixin):
    __tablename__ = "task_executions"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("scheduled_tasks.id"), nullable=True)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    status = Column(String(20), default="pending", comment="pending/running/passed/failed/error")
    total_cases = Column(Integer, default=0)
    passed_cases = Column(Integer, default=0)
    failed_cases = Column(Integer, default=0)
    duration = Column(Integer, comment="执行时长(秒)")
    log_output = Column(Text, comment="执行日志")
    report_data = Column(JSON, comment="报告数据")
    error_message = Column(Text)
    executor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    task = relationship("ScheduledTask", back_populates="executions")
    script = relationship("Script", back_populates="executions")

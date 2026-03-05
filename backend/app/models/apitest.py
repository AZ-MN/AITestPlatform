from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, JSON, Float
from sqlalchemy.orm import relationship
from app.db.base import Base, TimestampMixin


class ApiDefinition(Base, TimestampMixin):
    __tablename__ = "api_definitions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    module = Column(String(100), comment="接口模块")
    name = Column(String(200), nullable=False, comment="接口名称")
    method = Column(String(10), nullable=False, comment="GET/POST/PUT/DELETE/PATCH")
    path = Column(String(500), nullable=False, comment="接口路径")
    description = Column(Text)
    headers = Column(JSON, comment="请求头定义")
    query_params = Column(JSON, comment="Query参数定义")
    path_params = Column(JSON, comment="路径参数定义")
    body_schema = Column(JSON, comment="请求体JSON Schema")
    response_schema = Column(JSON, comment="响应体JSON Schema")
    source = Column(String(20), default="manual", comment="swagger/postman/manual")
    creator_id = Column(Integer, ForeignKey("users.id"))

    project = relationship("Project")
    api_cases = relationship("ApiCase", back_populates="api_definition")


class ApiCase(Base, TimestampMixin):
    __tablename__ = "api_cases"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    api_definition_id = Column(Integer, ForeignKey("api_definitions.id"), nullable=True)
    name = Column(String(200), nullable=False, comment="用例名称")
    description = Column(Text)
    headers = Column(JSON, comment="请求头")
    query_params = Column(JSON)
    path_params = Column(JSON)
    body = Column(JSON, comment="请求体")
    env = Column(String(20), default="test", comment="dev/test/prod")
    pre_script = Column(Text, comment="前置脚本")
    post_script = Column(Text, comment="后置脚本")
    assertions = Column(JSON, comment="断言列表 [{type, field, operator, value}]")
    case_type = Column(String(30), comment="normal/boundary/error/security")
    is_ai_generated = Column(Boolean, default=False)
    creator_id = Column(Integer, ForeignKey("users.id"))

    api_definition = relationship("ApiDefinition", back_populates="api_cases")


class ApiExecution(Base, TimestampMixin):
    __tablename__ = "api_executions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    api_case_id = Column(Integer, ForeignKey("api_cases.id"))
    iteration_id = Column(Integer, ForeignKey("iterations.id"), nullable=True)
    status = Column(String(20), comment="passed/failed/error")
    request_data = Column(JSON, comment="实际请求数据")
    response_status = Column(Integer, comment="HTTP状态码")
    response_body = Column(Text)
    response_headers = Column(JSON)
    response_time = Column(Float, comment="响应时间(ms)")
    assertion_results = Column(JSON, comment="断言结果列表")
    error_message = Column(Text)
    executor_id = Column(Integer, ForeignKey("users.id"))

    api_case = relationship("ApiCase")


class ApiScenario(Base, TimestampMixin):
    __tablename__ = "api_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(200), nullable=False, comment="场景名称")
    description = Column(Text)
    steps = Column(JSON, comment="步骤列表 [{api_case_id, name, extract_vars, assertions}]")
    creator_id = Column(Integer, ForeignKey("users.id"))

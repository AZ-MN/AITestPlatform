from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class ApiDefinitionBase(BaseModel):
    name: str
    method: str
    path: str
    module: Optional[str] = None
    description: Optional[str] = None
    headers: Optional[dict] = None
    query_params: Optional[dict] = None
    path_params: Optional[dict] = None
    body_schema: Optional[dict] = None
    response_schema: Optional[dict] = None


class ApiDefinitionCreate(ApiDefinitionBase):
    project_id: int
    source: str = "manual"


class ApiDefinitionOut(ApiDefinitionBase):
    id: int
    project_id: int
    source: str
    creator_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ApiCaseBase(BaseModel):
    name: str
    description: Optional[str] = None
    headers: Optional[dict] = None
    query_params: Optional[dict] = None
    path_params: Optional[dict] = None
    body: Optional[dict] = None
    env: str = "test"
    pre_script: Optional[str] = None
    post_script: Optional[str] = None
    assertions: Optional[list[dict]] = None
    case_type: Optional[str] = "normal"


class ApiCaseCreate(ApiCaseBase):
    project_id: int
    api_definition_id: Optional[int] = None


class ApiCaseOut(ApiCaseBase):
    id: int
    project_id: int
    api_definition_id: Optional[int] = None
    is_ai_generated: bool
    creator_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ApiDebugRequest(BaseModel):
    method: str
    url: str
    headers: Optional[dict] = None
    params: Optional[dict] = None
    body: Optional[Any] = None
    env: str = "test"
    timeout: int = 30


class ApiDebugResponse(BaseModel):
    status_code: int
    headers: dict
    body: Any
    response_time_ms: float
    size_bytes: int


class SwaggerImportRequest(BaseModel):
    project_id: int
    swagger_content: dict


class AiGenerateApiCasesRequest(BaseModel):
    project_id: int
    api_definition_id: int
    save_to_db: bool = True

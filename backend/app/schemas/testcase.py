from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class TestCaseStep(BaseModel):
    step: int
    action: str
    expected: str


class TestCaseCreate(BaseModel):
    project_id: int
    requirement_id: Optional[int] = None
    module: Optional[str] = None
    title: str
    case_level: str = "P1"
    test_type: str = "functional"
    stage: str = "system"
    preconditions: Optional[str] = None
    steps: Optional[List[Dict]] = None
    expected_results: Optional[List[str]] = None
    remarks: Optional[str] = None


class TestCaseUpdate(BaseModel):
    module: Optional[str] = None
    title: Optional[str] = None
    case_level: Optional[str] = None
    test_type: Optional[str] = None
    stage: Optional[str] = None
    preconditions: Optional[str] = None
    steps: Optional[List[Dict]] = None
    expected_results: Optional[List[str]] = None
    remarks: Optional[str] = None
    status: Optional[str] = None


class TestCaseOut(BaseModel):
    id: int
    project_id: int
    requirement_id: Optional[int]
    case_id: Optional[str]
    module: Optional[str]
    title: str
    case_level: str
    test_type: str
    stage: str
    preconditions: Optional[str]
    steps: Optional[List[Dict]]
    expected_results: Optional[List[str]]
    remarks: Optional[str]
    status: str
    ai_generated: int
    generation_batch: Optional[str]
    exec_status: Optional[str]
    rating: Optional[int]
    feedback: Optional[str]
    created_at: datetime
    updated_at: datetime
    creator_name: Optional[str] = None

    class Config:
        from_attributes = True


class GenerateRequest(BaseModel):
    project_id: int
    requirement_id: Optional[int] = None
    req_points: Optional[List[Dict]] = None  # 直接传入需求点
    test_type: str = "functional"            # functional / api / unit
    granularity: str = "medium"             # coarse / medium / fine
    priority_filter: Optional[str] = None   # 仅生成指定优先级的需求
    cover_scenarios: List[str] = ["normal", "exception", "boundary", "permission"]
    template_id: Optional[int] = None
    ai_provider: Optional[str] = None       # 使用哪个AI供应商
    temperature: float = 0.3
    custom_instructions: Optional[str] = None  # 用户补充的生成说明
    module_filter: Optional[str] = None     # 仅针对指定模块生成


class GenerateResponse(BaseModel):
    batch_id: str
    total: int
    cases: List[TestCaseOut]
    elapsed_seconds: float


class TestCaseRating(BaseModel):
    rating: int   # 1-5
    feedback: Optional[str] = None


class ExportRequest(BaseModel):
    project_id: int
    case_ids: Optional[List[int]] = None  # None = 导出全部
    format: str = "excel"                 # excel / markdown / csv
    requirement_id: Optional[int] = None


class AIModelConfigCreate(BaseModel):
    name: Optional[str] = None
    provider: str
    model_name: str
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    temperature: str = "0.3"
    max_tokens: int = 4096
    is_default: int = 0


class AIModelConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    temperature: Optional[str] = None
    max_tokens: Optional[int] = None
    is_default: Optional[int] = None


class AIModelConfigOut(BaseModel):
    id: int
    name: Optional[str] = None
    provider: str
    model_name: str
    api_base_url: Optional[str]
    temperature: str
    max_tokens: int
    is_default: int
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True

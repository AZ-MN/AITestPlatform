from pydantic import BaseModel
from typing import Optional


class ReportGenerateRequest(BaseModel):
    project_name: str
    iteration_name: str = "当前迭代"
    total_executions: int = 0
    passed: int = 0
    failed: int = 0
    defect_total: int = 0
    defect_open: int = 0
    defect_by_severity: Optional[dict] = None

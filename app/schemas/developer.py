from enum import Enum
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.schemas.architecture import StructuredSoftwareArchitecture, ApprovalStatusEnum, HumanApproval

class FileActionEnum(str, Enum):
    CREATE = "CREATE"
    MODIFY = "MODIFY"
    DELETE = "DELETE"

class FileTypeEnum(str, Enum):
    MODEL = "MODEL"
    SCHEMA = "SCHEMA"
    ROUTER = "ROUTER"
    SERVICE = "SERVICE"
    REPOSITORY = "REPOSITORY"
    CONFIG = "CONFIG"
    TEST = "TEST"
    MIGRATION = "MIGRATION"
    DOCUMENTATION = "DOCUMENTATION"

class FilePlan(BaseModel):
    file_path: str = Field(..., description="Relative path e.g. app/routers/customers.py")
    file_type: FileTypeEnum = FileTypeEnum.SERVICE
    action: FileActionEnum = FileActionEnum.CREATE
    purpose: str
    dependencies: List[str] = Field(default_factory=list)
    test_required: bool = True
    overwrite_allowed: bool = True

class ModulePlan(BaseModel):
    module_name: str
    module_path: str
    purpose: str
    files: List[FilePlan] = Field(default_factory=list)
    upstream_modules: List[str] = Field(default_factory=list)

class ImplementationPlan(BaseModel):
    project_slug: str
    target_framework: str = "FastAPI"
    modules: List[ModulePlan] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)
    total_files_planned: int = 0

class GeneratedFile(BaseModel):
    file_path: str
    file_type: FileTypeEnum
    action: FileActionEnum = FileActionEnum.CREATE
    language: str = "python"
    purpose: str
    content: str
    is_test_file: bool = False
    written_successfully: bool = False

class ValidationIssue(BaseModel):
    file_path: str
    line_number: Optional[int] = None
    issue_type: str = "SYNTAX_ERROR" # SYNTAX_ERROR, IMPORT_ERROR, ROUTE_ERROR, TYPE_ERROR
    message: str
    severity: Literal["ERROR", "WARNING"] = "ERROR"

class StaticValidationResult(BaseModel):
    is_valid: bool = True
    syntax_errors: List[ValidationIssue] = Field(default_factory=list)
    import_errors: List[ValidationIssue] = Field(default_factory=list)
    route_registration_valid: bool = True
    total_issues: int = 0

class TestCaseResult(BaseModel):
    __test__ = False
    test_name: str
    test_file: str
    status: Literal["PASSED", "FAILED", "SKIPPED", "ERROR"] = "PASSED"
    duration_seconds: float = 0.0
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None

class TestExecutionResult(BaseModel):
    __test__ = False
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    duration_seconds: float = 0.0
    all_passed: bool = True
    test_cases: List[TestCaseResult] = Field(default_factory=list)
    raw_output: str = ""

class FailureAnalysis(BaseModel):
    failing_test_names: List[str] = Field(default_factory=list)
    offending_files: List[str] = Field(default_factory=list)
    root_cause_summary: str
    recommended_patch: str
    is_architecture_issue: bool = False

class RepairAttempt(BaseModel):
    attempt_number: int
    repaired_files: List[str] = Field(default_factory=list)
    patch_description: str
    result_passed: bool = False
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ArchitectureDeviation(BaseModel):
    expected: str
    actual: str
    severity: Literal["CRITICAL", "WARNING"] = "WARNING"
    description: str

class ImplementationReport(BaseModel):
    project_name: str
    project_slug: str
    developer_task_id: str
    architect_task_id: str
    implementation_status: Literal["COMPLETED", "COMPLETED_WITH_WARNINGS", "REPAIRED", "BLOCKED", "FAILED"] = "COMPLETED"
    files_created: List[str] = Field(default_factory=list)
    files_modified: List[str] = Field(default_factory=list)
    tests_executed: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    repair_attempts_count: int = 0
    deviations: List[ArchitectureDeviation] = Field(default_factory=list)
    security_checklist_passed: bool = True
    human_approval: HumanApproval = Field(default_factory=HumanApproval)
    summary: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# API Requests & Responses
class DeveloperInputRequest(BaseModel):
    user_id: Optional[str] = "user_pramod_01"
    project_id: Optional[str] = "project_default_01"
    architect_task_id: Optional[str] = None
    approved_architecture: Optional[StructuredSoftwareArchitecture] = None
    workspace_directory: Optional[str] = None

class DeveloperResponse(BaseModel):
    developer_task_id: str
    architect_task_id: str
    project_id: str
    implementation_status: str
    human_approval: HumanApproval
    implementation_report: Optional[ImplementationReport] = None
    generated_files: List[str] = Field(default_factory=list)
    test_results: Optional[TestExecutionResult] = None
    errors: List[str] = Field(default_factory=list)
    retry_count: int = 0

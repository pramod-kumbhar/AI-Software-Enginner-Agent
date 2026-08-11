from enum import Enum
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

# 1. Enums
class CIFailureTypeEnum(str, Enum):
    TEST_FAILURE = "TEST_FAILURE"
    LINT_FAILURE = "LINT_FAILURE"
    TYPE_CHECK_FAILURE = "TYPE_CHECK_FAILURE"
    IMPORT_ERROR = "IMPORT_ERROR"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"
    BUILD_FAILURE = "BUILD_FAILURE"
    DOCKER_BUILD_FAILURE = "DOCKER_BUILD_FAILURE"
    DATABASE_MIGRATION_FAILURE = "DATABASE_MIGRATION_FAILURE"
    CONFIGURATION_FAILURE = "CONFIGURATION_FAILURE"
    ENVIRONMENT_FAILURE = "ENVIRONMENT_FAILURE"
    NETWORK_FAILURE = "NETWORK_FAILURE"
    AUTHENTICATION_FAILURE = "AUTHENTICATION_FAILURE"
    GITHUB_FAILURE = "GITHUB_FAILURE"
    TIMEOUT = "TIMEOUT"
    FLAKY_TEST = "FLAKY_TEST"
    UNKNOWN = "UNKNOWN"

class FailureSeverityEnum(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class RepairabilityEnum(str, Enum):
    AUTO_REPAIR_SAFE = "AUTO_REPAIR_SAFE"
    AUTO_REPAIR_WITH_APPROVAL = "AUTO_REPAIR_WITH_APPROVAL"
    NOT_REPAIRABLE = "NOT_REPAIRABLE"
    EXTERNAL_DEPENDENCY = "EXTERNAL_DEPENDENCY"
    UNKNOWN = "UNKNOWN"

class CIRunStatusEnum(str, Enum):
    CREATED = "CREATED"
    CI_PENDING = "CI_PENDING"
    CI_RUNNING = "CI_RUNNING"
    CI_PASSED = "CI_PASSED"
    CI_FAILED = "CI_FAILED"
    ANALYZING = "ANALYZING"
    REPAIR_PLANNED = "REPAIR_PLANNED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    REPAIRING = "REPAIRING"
    LOCAL_TESTING = "LOCAL_TESTING"
    QA_REVIEW = "QA_REVIEW"
    UPDATING_BRANCH = "UPDATING_BRANCH"
    CI_RETRY = "CI_RETRY"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

# 2. CI Job & Step Models
class CIStepInfo(BaseModel):
    name: str
    status: str
    conclusion: Optional[str] = None
    number: int
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class CIJobInfo(BaseModel):
    job_id: int
    job_name: str
    status: str # queued, in_progress, completed
    conclusion: Optional[str] = None # success, failure, cancelled
    failed_steps: List[str] = Field(default_factory=list)
    steps: List[CIStepInfo] = Field(default_factory=list)
    html_url: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

class CIWorkflowRun(BaseModel):
    run_id: int
    workflow_id: Optional[int] = None
    workflow_name: str = "CI"
    status: str
    conclusion: Optional[str] = None
    branch: str
    commit_sha: str
    html_url: str = ""
    jobs: List[CIJobInfo] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# 3. Strongly Typed Failure Model
class CIFailure(BaseModel):
    failure_id: str
    project_id: str
    developer_task_id: Optional[str] = None
    qa_task_id: Optional[str] = None
    github_repository: str
    branch: str
    pull_request_number: Optional[int] = None
    workflow_id: Optional[int] = None
    workflow_run_id: int
    job_id: int
    job_name: str
    failure_type: CIFailureTypeEnum = CIFailureTypeEnum.UNKNOWN
    severity: FailureSeverityEnum = FailureSeverityEnum.MEDIUM
    status: str = "DETECTED"
    failed_step: str = "test"
    error_summary: str = ""
    sanitized_log_excerpt: str = Field(default="", max_length=20000)
    root_cause: str = ""
    root_cause_confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    affected_files: List[str] = Field(default_factory=list)
    affected_tests: List[str] = Field(default_factory=list)
    repairability: RepairabilityEnum = RepairabilityEnum.AUTO_REPAIR_SAFE
    recommended_action: str = ""
    fingerprint: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# 4. Strongly Typed Repair Plan Model
class RepairPlan(BaseModel):
    repair_id: str
    failure_id: str
    project_id: str
    task_id: str
    summary: str
    root_cause: str
    affected_files: List[str] = Field(default_factory=list)
    required_changes: List[str] = Field(default_factory=list)
    tests_to_run: List[str] = Field(default_factory=list)
    risk_level: str = "LOW_RISK"
    estimated_complexity: str = "S" # XS, S, M, L
    approval_required: bool = False
    developer_instructions: str = ""
    rollback_strategy: str = "Revert to previous git commit and reset workspace."
    verification_plan: str = "Execute pytest on affected tests and run full local regression suite."
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# 5. Strongly Typed Repair Attempt & Result Models
class RepairAttempt(BaseModel):
    attempt_number: int
    repair_id: str
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    files_modified: List[str] = Field(default_factory=list)
    local_tests_passed: int = 0
    local_tests_failed: int = 0
    qa_score: float = 0.0
    commit_hash: Optional[str] = None
    ci_passed: bool = False
    error_message: Optional[str] = None

class RepairResult(BaseModel):
    repair_id: str
    failure_id: str
    status: CIRunStatusEnum = CIRunStatusEnum.CI_PASSED
    files_changed: List[str] = Field(default_factory=list)
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    qa_score: float = 100.0
    commit_sha: Optional[str] = None
    ci_run_id: Optional[int] = None
    remaining_issues: List[str] = Field(default_factory=list)
    attempt_number: int = 1
    max_attempts: int = 3
    is_blocked: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# 6. API Request & Response Models
class CIMonitorRequest(BaseModel):
    user_id: str = "user_default_01"
    project_id: str = "project_default_01"
    repository: str = "pramod-kumbhar/ai-software-engineer-agent"
    branch: str = "ai-agent/task-001"
    pull_request_number: Optional[int] = None
    workflow_run_id: Optional[int] = None
    workspace_directory: Optional[str] = None

class CIMonitorResponse(BaseModel):
    run_id: str
    status: CIRunStatusEnum
    workflow_run_id: int
    branch: str
    commit_sha: str
    failed_jobs: int = 0
    repair_attempt: int = 0
    max_attempts: int = 3
    failure: Optional[CIFailure] = None
    repair_plan: Optional[RepairPlan] = None
    repair_result: Optional[RepairResult] = None
    message: str = ""

class CIApprovalRequest(BaseModel):
    reviewer_name: str = "Lead_DevOps_Engineer"
    notes: Optional[str] = None

class RepairActionRequest(BaseModel):
    run_id: str
    force_retry: bool = False
    notes: Optional[str] = None

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class EnvironmentEnum(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class ReleaseStatusEnum(str, Enum):
    DRAFT = "DRAFT"
    VALIDATING = "VALIDATING"
    BLOCKED = "BLOCKED"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    STAGING_DEPLOYING = "STAGING_DEPLOYING"
    STAGING_VALIDATING = "STAGING_VALIDATING"
    PRODUCTION_APPROVAL_PENDING = "PRODUCTION_APPROVAL_PENDING"
    PRODUCTION_DEPLOYING = "PRODUCTION_DEPLOYING"
    HEALTH_CHECKING = "HEALTH_CHECKING"
    RELEASED = "RELEASED"
    ROLLBACK_PENDING = "ROLLBACK_PENDING"
    ROLLING_BACK = "ROLLING_BACK"
    ROLLED_BACK = "ROLLED_BACK"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class ReleaseDecisionEnum(str, Enum):
    DEPLOY = "DEPLOY"
    DEPLOY_WITH_APPROVAL = "DEPLOY_WITH_APPROVAL"
    BLOCK = "BLOCK"
    ROLLBACK = "ROLLBACK"

class RiskLevelEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ChangeCategoryEnum(str, Enum):
    FRONTEND = "FRONTEND"
    BACKEND = "BACKEND"
    DATABASE = "DATABASE"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    PAYMENT = "PAYMENT"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    CONFIGURATION = "CONFIGURATION"
    TEST = "TEST"
    DOCUMENTATION = "DOCUMENTATION"
    SECURITY = "SECURITY"
    DEPENDENCY = "DEPENDENCY"

class HealthStateEnum(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"

class HealthCheckResult(BaseModel):
    status: HealthStateEnum = HealthStateEnum.HEALTHY
    liveness: bool = True
    readiness: bool = True
    database: HealthStateEnum = HealthStateEnum.HEALTHY
    redis: HealthStateEnum = HealthStateEnum.HEALTHY
    dependencies: Dict[str, HealthStateEnum] = Field(default_factory=dict)
    latency_ms: float = 0.0
    version: str = "1.0.0"
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SmokeTestResult(BaseModel):
    test_name: str
    passed: bool
    duration_ms: float = 0.0
    error: Optional[str] = None

class DeploymentRun(BaseModel):
    deployment_id: str
    release_id: str
    version: str
    environment: EnvironmentEnum
    status: ReleaseStatusEnum = ReleaseStatusEnum.STAGING_DEPLOYING
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    deployed_by: str = "ReleaseAgent"
    health_status: HealthStateEnum = HealthStateEnum.HEALTHY
    smoke_test_results: List[SmokeTestResult] = Field(default_factory=list)
    rollback_triggered: bool = False
    error_message: Optional[str] = None

class RollbackEvent(BaseModel):
    rollback_id: str
    release_id: str
    failed_version: str
    target_rollback_version: str
    environment: EnvironmentEnum
    triggered_by: str = "AutonomousRollbackManager"
    reason: str
    status: ReleaseStatusEnum = ReleaseStatusEnum.ROLLED_BACK
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

class ReleaseManifest(BaseModel):
    release_id: str
    version: str
    project_id: str
    commit_sha: str
    branch: str
    pull_request_number: Optional[int] = None
    build_id: str = "build_default_01"
    artifact: str = "app-package-1.0.0.tar.gz"
    tests_passed: int = 0
    total_tests: int = 0
    qa_score: float = 100.0
    security_status: str = "PASS"
    architecture_status: str = "PASS"
    deployment_environment: EnvironmentEnum = EnvironmentEnum.STAGING
    rollback_version: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ReleaseReadiness(BaseModel):
    release_id: str
    version: str
    project_id: str
    task_id: Optional[str] = None
    commit_sha: str
    branch: str
    pull_request_number: Optional[int] = None
    ci_status: str = "PASS"
    qa_status: str = "PASS"
    qa_score: float = 100.0
    test_coverage: float = 100.0
    security_status: str = "PASS"
    architecture_status: str = "PASS"
    build_status: str = "PASS"
    artifact_status: str = "PASS"
    deployment_config_status: str = "PASS"
    health_check_status: HealthStateEnum = HealthStateEnum.HEALTHY
    risk_score: float = 0.0 # 0-100
    risk_level: RiskLevelEnum = RiskLevelEnum.LOW
    release_status: ReleaseStatusEnum = ReleaseStatusEnum.DRAFT
    decision: ReleaseDecisionEnum = ReleaseDecisionEnum.DEPLOY
    approval_status: str = "PENDING"
    blockers: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# Request / Response DTOs
class ReleaseCreateRequest(BaseModel):
    user_id: str = "user_default_01"
    project_id: str = "proj_default_01"
    commit_sha: str = "c0ffee1"
    branch: str = "main"
    pull_request_number: Optional[int] = None
    target_environment: EnvironmentEnum = EnvironmentEnum.STAGING
    version: Optional[str] = None

class ReleaseApprovalRequest(BaseModel):
    user_id: str
    role: str = "LEAD_DEVOPS"
    approved: bool
    comments: Optional[str] = None

class DeploymentRequest(BaseModel):
    user_id: str = "user_default_01"
    environment: EnvironmentEnum = EnvironmentEnum.STAGING
    force: bool = False

class RollbackRequest(BaseModel):
    user_id: str = "user_default_01"
    target_version: Optional[str] = None
    reason: str = "Manual operator emergency rollback request"
    environment: EnvironmentEnum = EnvironmentEnum.PRODUCTION

class ReleaseValidationResponse(BaseModel):
    release_id: str
    version: str
    environment: EnvironmentEnum
    ci_status: str
    qa_status: str
    qa_score: float
    security_status: str
    architecture_status: str
    artifact_status: str
    staging_status: str
    risk_score: float
    risk_level: RiskLevelEnum
    blockers: List[str]
    warnings: List[str]
    decision: ReleaseDecisionEnum
    approval_required: bool

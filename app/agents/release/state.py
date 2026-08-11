from typing import TypedDict, Optional, List, Dict, Any
from app.schemas.release import (
    ReleaseReadiness,
    ReleaseManifest,
    DeploymentRun,
    RollbackEvent,
    HealthCheckResult,
    ReleaseStatusEnum,
    ReleaseDecisionEnum,
    EnvironmentEnum
)

class ReleaseState(TypedDict, total=False):
    release_id: str
    project_id: str
    user_id: str
    commit_sha: str
    branch: str
    pull_request_number: Optional[int]
    version: str
    target_environment: EnvironmentEnum
    
    # Validation & Quality metrics
    ci_status: str
    qa_status: str
    qa_score: float
    test_coverage: float
    security_status: str
    architecture_status: str
    build_status: str
    artifact_status: str
    changed_files: List[str]
    diff_text: str
    
    # Computed Readiness & Risk
    readiness: Optional[ReleaseReadiness]
    release_manifest: Optional[ReleaseManifest]
    policy_decision: Optional[ReleaseDecisionEnum]
    approval_granted: bool
    approved_by: Optional[str]
    
    # Deployments
    staging_run: Optional[DeploymentRun]
    staging_health: Optional[HealthCheckResult]
    production_run: Optional[DeploymentRun]
    production_health: Optional[HealthCheckResult]
    rollback_event: Optional[RollbackEvent]
    
    # Output metadata
    status: ReleaseStatusEnum
    error: Optional[str]
    is_blocked: bool
    logs: List[str]

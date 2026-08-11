from typing import TypedDict, Optional, List, Dict, Any
from app.schemas.ci import (
    CIRunStatusEnum,
    CIWorkflowRun,
    CIFailure,
    RepairPlan,
    RepairAttempt,
    RepairResult
)

class CIMonitorState(TypedDict, total=False):
    # Workflow Execution & Context
    run_id: str
    project_id: str
    user_id: str
    repository: str
    branch: str
    pull_request_number: Optional[int]
    workflow_run_id: Optional[int]
    workspace_directory: str
    
    # State tracking
    current_step: str
    status: CIRunStatusEnum
    attempt_count: int
    max_attempts: int
    
    # CI Run Data
    workflow_run: Optional[CIWorkflowRun]
    failed_jobs: List[Dict[str, Any]]
    raw_failure_logs: str
    sanitized_failure_logs: str
    
    # Failure Analysis & Repair
    failure: Optional[CIFailure]
    repair_plan: Optional[RepairPlan]
    approval_granted: bool
    approval_reviewer: Optional[str]
    
    # Local & QA Verification
    modified_files: List[str]
    local_test_results: Dict[str, Any]
    qa_report: Optional[Dict[str, Any]]
    
    # Regression & Flaky Detection
    previous_test_results: Optional[Dict[str, Any]]
    is_regression: bool
    is_flaky: bool
    
    # Final Result & Errors
    repair_result: Optional[RepairResult]
    errors: List[str]

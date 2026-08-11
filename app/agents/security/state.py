from typing import TypedDict, List, Dict, Any, Optional
from app.schemas.security import (
    SecuritySeverityEnum,
    SecurityStatusEnum,
    SecurityDecisionEnum,
    SecurityFinding,
    ThreatModelEntry,
    SecurityRepairPlan,
    SecurityEventRecord
)

class SecurityState(TypedDict, total=False):
    # Context
    scan_id: str
    project_id: str
    user_id: str
    task_id: Optional[str]
    release_id: Optional[str]
    workspace_directory: str
    scan_type: str # FULL, PROMPT_ONLY, SECRET_ONLY
    
    # Analysis & Threat Model
    threat_model: List[ThreatModelEntry]
    findings: List[SecurityFinding]
    repaired_findings: List[SecurityFinding]
    
    # Gate & Scores
    security_score: float # 0 - 100
    status: SecurityStatusEnum
    decision: SecurityDecisionEnum
    blockers: List[str]
    
    # Repair State
    repair_plans: List[SecurityRepairPlan]
    repair_attempts: int
    max_repair_attempts: int
    is_blocked: bool
    approval_required: bool
    approved_by: Optional[str]
    
    # Audit & Telemetry
    events: List[SecurityEventRecord]
    error: Optional[str]

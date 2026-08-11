from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class SecuritySeverityEnum(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

class SecurityStatusEnum(str, Enum):
    SECURITY_READY = "SECURITY_READY"
    SECURITY_READY_WITH_WARNINGS = "SECURITY_READY_WITH_WARNINGS"
    NEEDS_SECURITY_FIXES = "NEEDS_SECURITY_FIXES"
    CRITICAL_SECURITY_BLOCK = "CRITICAL_SECURITY_BLOCK"

class SecurityDecisionEnum(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    BLOCK = "BLOCK"
    CRITICAL_BLOCK = "CRITICAL_BLOCK"

class SecurityCategoryEnum(str, Enum):
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    SECRETS = "SECRETS"
    FILESYSTEM = "FILESYSTEM"
    COMMAND_EXECUTION = "COMMAND_EXECUTION"
    MCP_SECURITY = "MCP_SECURITY"
    GIT_GITHUB = "GIT_GITHUB"
    CI_CD = "CI_CD"
    DEPENDENCIES = "DEPENDENCIES"
    CODE_SECURITY = "CODE_SECURITY"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    AUDITABILITY = "AUDITABILITY"
    DATA_ISOLATION = "DATA_ISOLATION"
    API_SECURITY = "API_SECURITY"
    DEPLOYMENT_SECURITY = "DEPLOYMENT_SECURITY"

class ThreatModelEntry(BaseModel):
    threat_id: str
    asset: str
    actor: str
    entry_point: str
    trust_boundary: str
    category: SecurityCategoryEnum
    description: str
    likelihood: str = "MEDIUM" # LOW, MEDIUM, HIGH
    impact: str = "HIGH"       # LOW, MEDIUM, HIGH, CRITICAL
    severity: SecuritySeverityEnum = SecuritySeverityEnum.HIGH
    attack_scenario: str
    existing_controls: List[str] = Field(default_factory=list)
    recommended_controls: List[str] = Field(default_factory=list)
    residual_risk: str = "LOW"
    status: str = "MITIGATED" # IDENTIFIED, MITIGATED, ACCEPTED
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class AgentPermission(BaseModel):
    agent_name: str
    resource: str
    action: str # read, write, execute, deploy, admin
    scope: str = "workspace" # workspace, global, system
    risk_level: str = "LOW"  # READ_ONLY, LOW, MEDIUM, HIGH, CRITICAL
    approval_required: bool = False
    enabled: bool = True

class SecurityFinding(BaseModel):
    finding_id: str
    category: SecurityCategoryEnum
    severity: SecuritySeverityEnum
    title: str
    description: str
    source: str = "STATIC_ANALYSIS" # STATIC_ANALYSIS, PROMPT_GUARD, SECRET_SCANNER, DEPENDENCY_CHECK
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    evidence: Optional[str] = None
    impact: str
    recommendation: str
    auto_fixable: bool = False
    approval_required: bool = False
    status: str = "OPEN" # OPEN, FIXED, SUPPRESSED, APPROVED
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SecurityRepairPlan(BaseModel):
    repair_id: str
    finding_id: str
    target_file: str
    root_cause: str
    required_change: str
    security_requirement: str
    is_auto_fixable: bool = True
    approval_required: bool = False
    approved_by: Optional[str] = None
    attempt_number: int = 1
    max_attempts: int = 3
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SecurityEventRecord(BaseModel):
    event_id: str
    event_type: str
    severity: SecuritySeverityEnum
    user_id: str = "system"
    project_id: str = "default_proj"
    agent_name: str = "SecurityAgent"
    tool_name: Optional[str] = None
    action: str = "SCAN"
    resource: Optional[str] = None
    decision: SecurityDecisionEnum = SecurityDecisionEnum.PASS
    reason: str
    trace_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class SecurityScanRequest(BaseModel):
    user_id: str = "user_default_01"
    project_id: str = "proj_default_01"
    task_id: Optional[str] = None
    release_id: Optional[str] = None
    scan_type: str = "FULL" # FULL, PROMPT_ONLY, SECRET_ONLY, DEPENDENCY_ONLY
    workspace_directory: Optional[str] = None

class SecurityScanResponse(BaseModel):
    scan_id: str
    project_id: str
    status: SecurityStatusEnum
    security_score: float # 0-100
    decision: SecurityDecisionEnum
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    blocking_issues: List[str] = Field(default_factory=list)
    findings: List[SecurityFinding] = Field(default_factory=list)
    threat_model: List[ThreatModelEntry] = Field(default_factory=list)
    approval_required: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

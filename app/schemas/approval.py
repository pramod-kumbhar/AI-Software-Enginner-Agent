from enum import Enum
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, Field
import hashlib
import json

class ApprovalTypeEnum(str, Enum):
    ARCHITECTURE_APPROVAL = "ARCHITECTURE_APPROVAL"
    CODE_APPROVAL = "CODE_APPROVAL"
    DATABASE_MIGRATION_APPROVAL = "DATABASE_MIGRATION_APPROVAL"
    SECURITY_APPROVAL = "SECURITY_APPROVAL"
    RELEASE_APPROVAL = "RELEASE_APPROVAL"
    PRODUCTION_DEPLOYMENT_APPROVAL = "PRODUCTION_DEPLOYMENT_APPROVAL"
    ROLLBACK_APPROVAL = "ROLLBACK_APPROVAL"
    HIGH_RISK_TOOL_APPROVAL = "HIGH_RISK_TOOL_APPROVAL"

class RiskLevelEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class AgentExecutionStatusEnum(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    WAITING_FOR_APPROVAL = "WAITING_FOR_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REWORK_REQUIRED = "REWORK_REQUIRED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    DEPLOYING = "DEPLOYING"
    ROLLED_BACK = "ROLLED_BACK"

class ApprovalDecisionEnum(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_CHANGES = "REQUEST_CHANGES"
    CANCEL = "CANCEL"

class ApprovalStatusEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"

class ReviewerRoleEnum(str, Enum):
    DEVELOPER = "DEVELOPER"
    TECH_LEAD = "TECH_LEAD"
    SECURITY_ENGINEER = "SECURITY_ENGINEER"
    RELEASE_MANAGER = "RELEASE_MANAGER"
    ADMIN = "ADMIN"

class ApprovalRequest(BaseModel):
    approval_id: str
    execution_id: str
    thread_id: str
    project_id: str
    task_id: str
    approval_type: ApprovalTypeEnum
    risk_level: RiskLevelEnum = RiskLevelEnum.HIGH
    requested_action: str
    action_summary: str
    action_details: Dict[str, Any] = Field(default_factory=dict)
    proposed_changes: List[str] = Field(default_factory=list)
    affected_files: List[str] = Field(default_factory=list)
    security_impact: str = "No critical security vulnerabilities identified."
    estimated_cost: float = 0.0
    required_role: ReviewerRoleEnum = ReviewerRoleEnum.TECH_LEAD
    status: ApprovalStatusEnum = ApprovalStatusEnum.PENDING
    requested_by: str = "Agent"
    reviewed_by: Optional[str] = None
    reviewer_role: Optional[ReviewerRoleEnum] = None
    review_comment: Optional[str] = None
    rejection_reason: Optional[str] = None
    action_hash: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str = Field(default_factory=lambda: (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat())
    resolved_at: Optional[str] = None

    def calculate_action_hash(self) -> str:
        payload = {
            "requested_action": self.requested_action,
            "action_summary": self.action_summary,
            "proposed_changes": sorted(self.proposed_changes),
            "affected_files": sorted(self.affected_files),
            "approval_type": self.approval_type.value,
            "risk_level": self.risk_level.value
        }
        encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

class ApprovalDecisionRequest(BaseModel):
    decision: ApprovalDecisionEnum
    reviewer_id: str
    reviewer_role: ReviewerRoleEnum
    feedback: Optional[str] = None
    action_hash: Optional[str] = None

class ApprovalDecisionRecord(BaseModel):
    decision_id: str
    approval_id: str
    execution_id: str
    actor_id: str
    actor_role: ReviewerRoleEnum
    decision: ApprovalDecisionEnum
    feedback: Optional[str] = None
    action_hash: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class TimelineEvent(BaseModel):
    event_id: str
    execution_id: str
    thread_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    node: str
    event: str
    status: str
    actor: str = "System"
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReworkRecord(BaseModel):
    rework_id: str
    execution_id: str
    approval_id: str
    phase: str
    attempt_number: int
    feedback: str
    previous_output: Dict[str, Any] = Field(default_factory=dict)
    new_output: Optional[Dict[str, Any]] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ToolApprovalPolicy(BaseModel):
    tool_name: str
    risk_level: RiskLevelEnum
    requires_approval: bool = True
    required_role: ReviewerRoleEnum = ReviewerRoleEnum.DEVELOPER
    max_calls_per_task: int = 10
    allowed_environments: List[str] = Field(default_factory=lambda: ["development", "test", "staging"])

class AgentExecutionCreateRequest(BaseModel):
    prompt: str
    project_id: str = "proj_default"
    user_id: str = "user_default"
    task_id: Optional[str] = None
    auto_approve_low_risk: bool = True

class AgentResumeRequest(BaseModel):
    approval_decision: Optional[ApprovalDecisionRequest] = None
    user_feedback: Optional[str] = None

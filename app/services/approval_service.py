import threading
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from app.schemas.approval import (
    ApprovalRequest,
    ApprovalDecisionRequest,
    ApprovalDecisionRecord,
    ApprovalTypeEnum,
    ApprovalStatusEnum,
    ApprovalDecisionEnum,
    RiskLevelEnum,
    ReviewerRoleEnum
)
from app.core.logger import get_logger
from app.core.config import settings

logger = get_logger("approval_service")

class ApprovalServiceError(Exception):
    """Base exception for approval service errors."""
    pass

class UnauthorizedApproverError(ApprovalServiceError):
    """Raised when reviewer role does not have permission to approve the action."""
    pass

class SeparationOfDutiesError(ApprovalServiceError):
    """Raised when the creator attempts to approve their own high-risk action."""
    pass

class StaleApprovalError(ApprovalServiceError):
    """Raised when the action hash does not match the approved hash."""
    pass

class ApprovalExpiredError(ApprovalServiceError):
    """Raised when attempting to resolve an expired approval request."""
    pass

class ApprovalService:
    """
    Production Human-in-the-Loop Approval & Authorization Engine.
    Handles cryptographic action hashing, role authorization, separation of duties,
    idempotent decision recording, and stale approval fencing.
    """
    _instance = None
    _lock = threading.Lock()

    # Role hierarchy: ADMIN > RELEASE_MANAGER > SECURITY_ENGINEER > TECH_LEAD > DEVELOPER
    ROLE_HIERARCHY: Dict[ReviewerRoleEnum, int] = {
        ReviewerRoleEnum.DEVELOPER: 1,
        ReviewerRoleEnum.TECH_LEAD: 2,
        ReviewerRoleEnum.SECURITY_ENGINEER: 3,
        ReviewerRoleEnum.RELEASE_MANAGER: 4,
        ReviewerRoleEnum.ADMIN: 5
    }

    TYPE_ROLE_MAP: Dict[ApprovalTypeEnum, ReviewerRoleEnum] = {
        ApprovalTypeEnum.ARCHITECTURE_APPROVAL: ReviewerRoleEnum.TECH_LEAD,
        ApprovalTypeEnum.CODE_APPROVAL: ReviewerRoleEnum.DEVELOPER,
        ApprovalTypeEnum.DATABASE_MIGRATION_APPROVAL: ReviewerRoleEnum.TECH_LEAD,
        ApprovalTypeEnum.SECURITY_APPROVAL: ReviewerRoleEnum.SECURITY_ENGINEER,
        ApprovalTypeEnum.RELEASE_APPROVAL: ReviewerRoleEnum.RELEASE_MANAGER,
        ApprovalTypeEnum.PRODUCTION_DEPLOYMENT_APPROVAL: ReviewerRoleEnum.RELEASE_MANAGER,
        ApprovalTypeEnum.ROLLBACK_APPROVAL: ReviewerRoleEnum.RELEASE_MANAGER,
        ApprovalTypeEnum.HIGH_RISK_TOOL_APPROVAL: ReviewerRoleEnum.TECH_LEAD,
    }

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ApprovalService, cls).__new__(cls)
                cls._instance._approvals: Dict[str, ApprovalRequest] = {}
                cls._instance._decisions: List[ApprovalDecisionRecord] = []
            return cls._instance

    def create_approval_request(
        self,
        execution_id: str,
        thread_id: str,
        project_id: str,
        task_id: str,
        approval_type: ApprovalTypeEnum,
        risk_level: RiskLevelEnum,
        requested_action: str,
        action_summary: str,
        action_details: Optional[Dict[str, Any]] = None,
        proposed_changes: Optional[List[str]] = None,
        affected_files: Optional[List[str]] = None,
        security_impact: str = "No critical security vulnerabilities identified.",
        estimated_cost: float = 0.0,
        requested_by: str = "Agent",
        expires_in_hours: int = 24
    ) -> ApprovalRequest:
        """Create and register a strongly-typed approval request with action hash."""
        with self._lock:
            approval_id = f"appr_{uuid.uuid4().hex[:12]}"
            required_role = self.TYPE_ROLE_MAP.get(approval_type, ReviewerRoleEnum.TECH_LEAD)
            
            # High / Critical risk escalates code approval to Tech Lead or Admin
            if approval_type == ApprovalTypeEnum.CODE_APPROVAL and risk_level in [RiskLevelEnum.HIGH, RiskLevelEnum.CRITICAL]:
                required_role = ReviewerRoleEnum.TECH_LEAD

            now = datetime.now(timezone.utc)
            expires_at = (now + timedelta(hours=expires_in_hours)).isoformat()

            req = ApprovalRequest(
                approval_id=approval_id,
                execution_id=execution_id,
                thread_id=thread_id,
                project_id=project_id,
                task_id=task_id,
                approval_type=approval_type,
                risk_level=risk_level,
                requested_action=requested_action,
                action_summary=action_summary,
                action_details=action_details or {},
                proposed_changes=proposed_changes or [],
                affected_files=affected_files or [],
                security_impact=security_impact,
                estimated_cost=estimated_cost,
                required_role=required_role,
                status=ApprovalStatusEnum.PENDING,
                requested_by=requested_by,
                created_at=now.isoformat(),
                expires_at=expires_at
            )
            req.action_hash = req.calculate_action_hash()
            self._approvals[approval_id] = req
            
            logger.info(
                f"APPROVAL REQUEST CREATED: [{req.approval_id}] Type={req.approval_type.value} "
                f"Risk={req.risk_level.value} RoleReq={req.required_role.value} Hash={req.action_hash[:8]}..."
            )
            return req

    def get_approval(self, approval_id: str) -> Optional[ApprovalRequest]:
        with self._lock:
            req = self._approvals.get(approval_id)
            if not req:
                return None
            # Check expiration dynamically
            self._check_and_update_expiration(req)
            return req

    def list_approvals(
        self,
        project_id: Optional[str] = None,
        status: Optional[ApprovalStatusEnum] = None
    ) -> List[ApprovalRequest]:
        with self._lock:
            results = []
            for req in self._approvals.values():
                self._check_and_update_expiration(req)
                if project_id and req.project_id != project_id:
                    continue
                if status and req.status != status:
                    continue
                results.append(req)
            return sorted(results, key=lambda x: x.created_at, reverse=True)

    def resolve_approval(
        self,
        approval_id: str,
        decision_req: ApprovalDecisionRequest
    ) -> ApprovalRequest:
        """
        Idempotently resolve an approval request enforcing RBAC, Separation of Duties,
        Expiration checks, and Action Hash validation.
        """
        with self._lock:
            req = self._approvals.get(approval_id)
            if not req:
                raise ApprovalServiceError(f"Approval request '{approval_id}' not found.")

            self._check_and_update_expiration(req)

            # 1. Expiration Check
            if req.status == ApprovalStatusEnum.EXPIRED:
                raise ApprovalExpiredError(f"Approval request '{approval_id}' has expired and cannot be resolved.")

            # 2. Idempotency Check
            if req.status != ApprovalStatusEnum.PENDING:
                # If resolved with same decision, return current state safely
                mapped_status = self._decision_to_status(decision_req.decision)
                if req.status == mapped_status:
                    logger.info(f"IDEMPOTENT RESOLUTION: Approval '{approval_id}' already resolved to {req.status.value}.")
                    return req
                raise ApprovalServiceError(
                    f"Approval request '{approval_id}' is already resolved with status '{req.status.value}'."
                )

            # 3. Separation of Duties (Creator cannot approve their own high-risk request)
            if req.requested_by.lower() == decision_req.reviewer_id.lower() and req.risk_level in [RiskLevelEnum.HIGH, RiskLevelEnum.CRITICAL]:
                raise SeparationOfDutiesError(
                    f"Separation of duties violation: '{decision_req.reviewer_id}' created this high-risk request and cannot approve it."
                )

            # 4. Role Authorization Check
            if not self._is_authorized_role(decision_req.reviewer_role, req.required_role):
                raise UnauthorizedApproverError(
                    f"Role '{decision_req.reviewer_role.value}' is not authorized to resolve {req.approval_type.value}. "
                    f"Required role: '{req.required_role.value}'."
                )

            # 5. Stale Approval / Action Hash Protection
            if decision_req.action_hash and decision_req.action_hash != req.action_hash:
                raise StaleApprovalError(
                    f"Stale approval detected! Action hash mismatch. Approved hash: '{decision_req.action_hash[:8]}', "
                    f"Current action hash: '{req.action_hash[:8]}'."
                )

            # 6. Apply Decision
            now_iso = datetime.now(timezone.utc).isoformat()
            req.status = self._decision_to_status(decision_req.decision)
            req.reviewed_by = decision_req.reviewer_id
            req.reviewer_role = decision_req.reviewer_role
            req.review_comment = decision_req.feedback
            req.resolved_at = now_iso
            if decision_req.decision in [ApprovalDecisionEnum.REJECT, ApprovalDecisionEnum.REQUEST_CHANGES]:
                req.rejection_reason = decision_req.feedback

            # 7. Record Decision Audit Entry
            decision_record = ApprovalDecisionRecord(
                decision_id=f"dec_{uuid.uuid4().hex[:12]}",
                approval_id=req.approval_id,
                execution_id=req.execution_id,
                actor_id=decision_req.reviewer_id,
                actor_role=decision_req.reviewer_role,
                decision=decision_req.decision,
                feedback=decision_req.feedback,
                action_hash=req.action_hash,
                created_at=now_iso
            )
            self._decisions.append(decision_record)

            logger.info(
                f"APPROVAL RESOLVED: [{req.approval_id}] -> {req.status.value} by {decision_req.reviewer_id} "
                f"({decision_req.reviewer_role.value})"
            )
            return req

    def list_decision_history(self, execution_id: Optional[str] = None) -> List[ApprovalDecisionRecord]:
        with self._lock:
            if execution_id:
                return [d for d in self._decisions if d.execution_id == execution_id]
            return list(self._decisions)

    def _is_authorized_role(self, reviewer_role: ReviewerRoleEnum, required_role: ReviewerRoleEnum) -> bool:
        if reviewer_role == ReviewerRoleEnum.ADMIN:
            return True
        reviewer_rank = self.ROLE_HIERARCHY.get(reviewer_role, 0)
        required_rank = self.ROLE_HIERARCHY.get(required_role, 0)
        return reviewer_rank >= required_rank

    def _decision_to_status(self, decision: ApprovalDecisionEnum) -> ApprovalStatusEnum:
        mapping = {
            ApprovalDecisionEnum.APPROVE: ApprovalStatusEnum.APPROVED,
            ApprovalDecisionEnum.REJECT: ApprovalStatusEnum.REJECTED,
            ApprovalDecisionEnum.REQUEST_CHANGES: ApprovalStatusEnum.CHANGES_REQUESTED,
            ApprovalDecisionEnum.CANCEL: ApprovalStatusEnum.CANCELLED
        }
        return mapping.get(decision, ApprovalStatusEnum.REJECTED)

    def _check_and_update_expiration(self, req: ApprovalRequest) -> None:
        if req.status == ApprovalStatusEnum.PENDING and req.expires_at:
            try:
                exp_dt = datetime.fromisoformat(req.expires_at)
                if datetime.now(timezone.utc) > exp_dt:
                    req.status = ApprovalStatusEnum.EXPIRED
                    req.resolved_at = datetime.now(timezone.utc).isoformat()
                    logger.warning(f"APPROVAL EXPIRED: [{req.approval_id}] expired at {req.expires_at}")
            except Exception:
                pass

approval_service = ApprovalService()

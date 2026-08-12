import pytest
from app.services.approval_service import (
    ApprovalService,
    UnauthorizedApproverError,
    SeparationOfDutiesError,
    StaleApprovalError,
    ApprovalExpiredError,
    ApprovalServiceError
)
from app.schemas.approval import (
    ApprovalTypeEnum,
    RiskLevelEnum,
    ReviewerRoleEnum,
    ApprovalDecisionEnum,
    ApprovalDecisionRequest,
    ApprovalStatusEnum
)

@pytest.fixture
def approval_svc():
    return ApprovalService()

def test_create_approval_request_with_hash(approval_svc):
    req = approval_svc.create_approval_request(
        execution_id="exec_test_01",
        thread_id="thread_test_01",
        project_id="proj_01",
        task_id="task_01",
        approval_type=ApprovalTypeEnum.ARCHITECTURE_APPROVAL,
        risk_level=RiskLevelEnum.HIGH,
        requested_action="Authorize Architecture",
        action_summary="Approve Microservices Blueprint",
        proposed_changes=["Add PostgreSQL", "Add Redis Cache"],
        affected_files=["app/main.py", "app/models/user.py"],
        requested_by="ArchitectAgent"
    )
    assert req.approval_id.startswith("appr_")
    assert req.status == ApprovalStatusEnum.PENDING
    assert req.required_role == ReviewerRoleEnum.TECH_LEAD
    assert req.action_hash is not None
    assert len(req.action_hash) == 64

def test_role_authorization_blocks_insufficient_role(approval_svc):
    req = approval_svc.create_approval_request(
        execution_id="exec_test_02",
        thread_id="thread_test_02",
        project_id="proj_01",
        task_id="task_02",
        approval_type=ApprovalTypeEnum.ARCHITECTURE_APPROVAL, # Requires TECH_LEAD
        risk_level=RiskLevelEnum.HIGH,
        requested_action="Authorize Architecture",
        action_summary="Architecture change",
        requested_by="ArchitectAgent"
    )
    
    # DEVELOPER trying to approve TECH_LEAD level action
    decision_req = ApprovalDecisionRequest(
        decision=ApprovalDecisionEnum.APPROVE,
        reviewer_id="dev_alice",
        reviewer_role=ReviewerRoleEnum.DEVELOPER,
        action_hash=req.action_hash
    )
    with pytest.raises(UnauthorizedApproverError):
        approval_svc.resolve_approval(req.approval_id, decision_req)

def test_separation_of_duties_blocks_self_approval(approval_svc):
    req = approval_svc.create_approval_request(
        execution_id="exec_test_03",
        thread_id="thread_test_03",
        project_id="proj_01",
        task_id="task_03",
        approval_type=ApprovalTypeEnum.PRODUCTION_DEPLOYMENT_APPROVAL,
        risk_level=RiskLevelEnum.CRITICAL,
        requested_action="Deploy to Production",
        action_summary="Production deployment",
        requested_by="user_charlie" # Creator
    )

    # user_charlie attempts to approve their own critical deployment
    decision_req = ApprovalDecisionRequest(
        decision=ApprovalDecisionEnum.APPROVE,
        reviewer_id="user_charlie",
        reviewer_role=ReviewerRoleEnum.RELEASE_MANAGER,
        action_hash=req.action_hash
    )
    with pytest.raises(SeparationOfDutiesError):
        approval_svc.resolve_approval(req.approval_id, decision_req)

def test_stale_approval_hash_mismatch(approval_svc):
    req = approval_svc.create_approval_request(
        execution_id="exec_test_04",
        thread_id="thread_test_04",
        project_id="proj_01",
        task_id="task_04",
        approval_type=ApprovalTypeEnum.ARCHITECTURE_APPROVAL,
        risk_level=RiskLevelEnum.HIGH,
        requested_action="Authorize Architecture",
        action_summary="Original Architecture",
        requested_by="ArchitectAgent"
    )

    # Reviewer passes outdated hash
    decision_req = ApprovalDecisionRequest(
        decision=ApprovalDecisionEnum.APPROVE,
        reviewer_id="tech_lead_dan",
        reviewer_role=ReviewerRoleEnum.TECH_LEAD,
        action_hash="outdated_stale_hash_1234567890abcdef"
    )
    with pytest.raises(StaleApprovalError):
        approval_svc.resolve_approval(req.approval_id, decision_req)

def test_idempotent_approval_resolution(approval_svc):
    req = approval_svc.create_approval_request(
        execution_id="exec_test_05",
        thread_id="thread_test_05",
        project_id="proj_01",
        task_id="task_05",
        approval_type=ApprovalTypeEnum.ARCHITECTURE_APPROVAL,
        risk_level=RiskLevelEnum.HIGH,
        requested_action="Authorize Architecture",
        action_summary="Original Architecture",
        requested_by="ArchitectAgent"
    )

    decision_req = ApprovalDecisionRequest(
        decision=ApprovalDecisionEnum.APPROVE,
        reviewer_id="tech_lead_dan",
        reviewer_role=ReviewerRoleEnum.TECH_LEAD,
        action_hash=req.action_hash
    )

    # 1. First approval
    res1 = approval_svc.resolve_approval(req.approval_id, decision_req)
    assert res1.status == ApprovalStatusEnum.APPROVED

    # 2. Second duplicate approval is idempotent
    res2 = approval_svc.resolve_approval(req.approval_id, decision_req)
    assert res2.status == ApprovalStatusEnum.APPROVED
    assert res2.reviewed_by == "tech_lead_dan"

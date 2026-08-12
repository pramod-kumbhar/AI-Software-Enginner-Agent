import pytest
from app.agents.orchestrator.graph import master_orchestrator
from app.schemas.approval import (
    ApprovalDecisionRequest,
    ApprovalDecisionEnum,
    ReviewerRoleEnum,
    AgentExecutionStatusEnum,
    ApprovalStatusEnum
)
from app.services.storage import storage_service
from app.services.timeline_service import timeline_service

@pytest.mark.asyncio
async def test_hitl_full_lifecycle_with_rework_and_deployment():
    # 1. Start execution -> should pause at Human Architecture Approval Gate
    state1 = await master_orchestrator.start_execution(
        prompt="Build a high-performance inventory management API",
        project_id="proj_hitl_test_01",
        user_id="user_alice"
    )
    assert state1["status"] == AgentExecutionStatusEnum.WAITING_FOR_APPROVAL.value
    assert state1["current_phase"] == "WAITING_FOR_ARCHITECTURE_APPROVAL"
    assert state1["approval_required"] is True
    assert state1["approval_id"] is not None
    arch_appr_id = state1["approval_id"]

    # 2. Human requests changes / rejects with feedback
    dec_rework = ApprovalDecisionRequest(
        decision=ApprovalDecisionEnum.REQUEST_CHANGES,
        reviewer_id="tech_lead_bob",
        reviewer_role=ReviewerRoleEnum.TECH_LEAD,
        feedback="Use PostgreSQL 16 with TimescaleDB extension.",
        action_hash=state1["action_hash"]
    )
    state2 = await master_orchestrator.resume_execution(state1["execution_id"], dec_rework)
    assert state2["rework_count"] >= 1
    assert state2["status"] == AgentExecutionStatusEnum.WAITING_FOR_APPROVAL.value # Paused at new approval gate
    assert state2["approval_id"] != arch_appr_id # New approval request generated

    # 3. Human approves the reworked architecture
    new_arch_appr_id = state2["approval_id"]
    dec_approve_arch = ApprovalDecisionRequest(
        decision=ApprovalDecisionEnum.APPROVE,
        reviewer_id="tech_lead_bob",
        reviewer_role=ReviewerRoleEnum.TECH_LEAD,
        feedback="Architecture verified and approved.",
        action_hash=state2["action_hash"]
    )
    state3 = await master_orchestrator.resume_execution(state2["execution_id"], dec_approve_arch)
    
    # 4. Agent proceeds through Developer, QA, Security, Release, and reaches Deployment Approval Gate
    assert state3["current_phase"] == "WAITING_FOR_DEPLOYMENT_APPROVAL"
    assert state3["status"] == AgentExecutionStatusEnum.WAITING_FOR_APPROVAL.value
    assert len(state3["generated_files"]) > 0
    assert state3["test_results"]["status"] == "PASS"
    assert state3["security_results"]["status"] == "PASS"
    deploy_appr_id = state3["approval_id"]
    assert deploy_appr_id != new_arch_appr_id

    # 5. Release Manager approves Production Deployment
    dec_approve_deploy = ApprovalDecisionRequest(
        decision=ApprovalDecisionEnum.APPROVE,
        reviewer_id="rel_mgr_charlie",
        reviewer_role=ReviewerRoleEnum.RELEASE_MANAGER,
        feedback="Production rollout approved.",
        action_hash=state3["action_hash"]
    )
    state4 = await master_orchestrator.resume_execution(state3["execution_id"], dec_approve_deploy)

    # 6. Deployment executes and workflow completes
    assert state4["status"] == AgentExecutionStatusEnum.COMPLETED.value
    assert state4["current_phase"] == "COMPLETED"
    assert state4["deployment_plan"]["status"] == "DEPLOYED"

    # 7. Check timeline events
    timeline = timeline_service.get_timeline(state1["execution_id"])
    assert len(timeline) >= 8

@pytest.mark.asyncio
async def test_hitl_pause_and_cancel_lifecycle():
    state1 = await master_orchestrator.start_execution(
        prompt="Build customer notification service",
        project_id="proj_hitl_pause_01",
        user_id="user_alice"
    )
    exec_id = state1["execution_id"]

    # Pause execution
    paused_state = await master_orchestrator.pause_execution(exec_id)
    assert paused_state["status"] == AgentExecutionStatusEnum.PAUSED.value

    # Cancel execution
    cancelled_state = await master_orchestrator.cancel_execution(exec_id, reason="User terminated task")
    assert cancelled_state["status"] == AgentExecutionStatusEnum.CANCELLED.value

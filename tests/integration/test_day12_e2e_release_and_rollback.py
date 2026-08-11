import pytest
from app.agents.release.graph import release_agent
from app.schemas.release import (
    ReleaseStatusEnum,
    ReleaseDecisionEnum,
    EnvironmentEnum
)
from app.services.deployment_providers import deployment_provider
from app.services.storage import storage_service

@pytest.mark.asyncio
async def test_day12_e2e_successful_release_workflow():
    """
    End-to-End Successful Release Workflow:
    1. Release context loaded with high QA score (95/100).
    2. CI, QA, Security, Architecture & Artifact validated.
    3. Release risk score calculated.
    4. Deterministic policy approves deployment.
    5. Staging deployment executed and smoke tests pass.
    6. Human approval granted for production.
    7. Production deployed, health verified -> Status = RELEASED.
    """
    initial_state = {
        "release_id": "rel_e2e_success_01",
        "version": "1.0.0",
        "project_id": "proj_task_mgr_e2e",
        "user_id": "user_devops_01",
        "commit_sha": "f1a2b3c",
        "branch": "main",
        "target_environment": EnvironmentEnum.PRODUCTION,
        "approval_granted": True,
        "approved_by": "LeadDevOps",
        "qa_score": 95.0,
        "ci_status": "PASS",
        "qa_status": "PASS",
        "security_status": "PASS",
        "architecture_status": "PASS"
    }

    config = {"configurable": {"thread_id": "sess_e2e_release_01"}}
    final_state = await release_agent.ainvoke(initial_state, config=config)

    assert final_state["status"] == ReleaseStatusEnum.RELEASED
    assert final_state["is_blocked"] is False
    assert final_state.get("production_run") is not None
    assert final_state["production_run"].status == ReleaseStatusEnum.RELEASED

@pytest.mark.asyncio
async def test_day12_e2e_health_failure_and_rollback():
    """
    End-to-End Failure & Rollback Workflow:
    1. Version 1.0.0 exists as known-good baseline.
    2. Version 1.1.0 deployed to production.
    3. Live production health probe fails (database / latency failure).
    4. Release Agent detects failure and triggers autonomous rollback.
    5. Rollback restores version 1.0.0 -> Status = ROLLED_BACK.
    """
    # Seed baseline release 1.0.0
    storage_service.save_release("rel_v1_baseline", {
        "release_id": "rel_v1_baseline",
        "version": "1.0.0",
        "release_status": ReleaseStatusEnum.RELEASED.value
    })

    # Simulate production health degradation
    deployment_provider.simulate_production_health_failure = True

    initial_state = {
        "release_id": "rel_v2_failing",
        "version": "1.1.0",
        "project_id": "proj_task_mgr_e2e",
        "user_id": "user_devops_01",
        "commit_sha": "d4e5f6a",
        "branch": "main",
        "target_environment": EnvironmentEnum.PRODUCTION,
        "approval_granted": True,
        "approved_by": "LeadDevOps",
        "qa_score": 95.0,
        "ci_status": "PASS",
        "qa_status": "PASS",
        "security_status": "PASS",
        "architecture_status": "PASS"
    }

    try:
        config = {"configurable": {"thread_id": "sess_e2e_rollback_01"}}
        final_state = await release_agent.ainvoke(initial_state, config=config)

        assert final_state["status"] == ReleaseStatusEnum.ROLLED_BACK
        assert final_state.get("rollback_event") is not None
        assert final_state["rollback_event"].target_rollback_version == "1.0.0"
    finally:
        deployment_provider.simulate_production_health_failure = False


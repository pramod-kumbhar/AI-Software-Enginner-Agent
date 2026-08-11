import pytest
from app.core.agent_auth import agent_auth

def test_deny_by_default_blocks_unregistered_actions():
    # Planner attempting to write to workspace
    allowed, reason = agent_auth.check_permission("PlannerAgent", "workspace", "write")
    assert allowed is False
    assert "DENY BY DEFAULT" in reason

def test_developer_agent_workspace_write_allowed():
    allowed, reason = agent_auth.check_permission("DeveloperAgent", "workspace", "write")
    assert allowed is True

def test_production_deployment_requires_human_approval():
    # ReleaseAgent attempting prod deploy without approval
    allowed, reason = agent_auth.check_permission("ReleaseAgent", "deployment", "production", approval_granted=False)
    assert allowed is False
    assert "HUMAN APPROVAL REQUIRED" in reason

    # With approval
    allowed_with_app, _ = agent_auth.check_permission("ReleaseAgent", "deployment", "production", approval_granted=True)
    assert allowed_with_app is True

def test_cross_tenant_access_blocked():
    # User A attempting to access User B project
    allowed, reason = agent_auth.check_tenant_isolation(
        requester_user_id="user_alice",
        target_user_id="user_bob",
        requester_project_id="proj_alice_01",
        target_project_id="proj_bob_01"
    )
    assert allowed is False
    assert "CROSS-USER ACCESS DENIED" in reason

def test_cross_project_access_blocked():
    # Same user attempting to cross project boundary
    allowed, reason = agent_auth.check_tenant_isolation(
        requester_user_id="user_alice",
        target_user_id="user_alice",
        requester_project_id="proj_alice_01",
        target_project_id="proj_alice_02"
    )
    assert allowed is False
    assert "CROSS-PROJECT ACCESS DENIED" in reason

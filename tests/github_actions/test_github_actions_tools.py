import pytest
from app.mcp.client import MCPClient
from app.mcp.schemas import RiskLevelEnum

@pytest.mark.asyncio
async def test_mcp_github_actions_tools():
    client = MCPClient(agent_name="TestDevOpsAgent", role="DEVELOPER")
    
    # 1. CI Status
    ci_status = await client.call_tool("github.get_ci_status", {
        "repository": "pramod-kumbhar/ai-software-engineer-agent",
        "branch": "main"
    })
    assert ci_status.is_success is True
    assert "status" in ci_status.result

    # 2. Failed Jobs
    failed_jobs = await client.call_tool("github.get_failed_jobs", {
        "workflow_run_id": 100201
    })
    assert failed_jobs.is_success is True
    assert isinstance(failed_jobs.result, list)

    # 3. Failure Logs
    logs = await client.call_tool("github.get_failure_logs", {
        "workflow_run_id": 100201,
        "job_id": 2002,
        "max_chars": 2000
    })
    assert logs.is_success is True
    assert "sanitized_log_excerpt" in logs.result

    # 4. Trigger CI
    trigger = await client.call_tool("github.trigger_ci", {
        "repository": "pramod-kumbhar/ai-software-engineer-agent",
        "branch": "main"
    })
    assert trigger.is_success is True
    assert trigger.result.get("triggered") is True

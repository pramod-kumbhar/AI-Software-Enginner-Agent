import pytest
from app.tools.github.actions_handlers import GitHubActionsToolHandlers

@pytest.mark.asyncio
async def test_github_actions_get_ci_status():
    status = await GitHubActionsToolHandlers.get_ci_status(
        repository="pramod-kumbhar/ai-software-engineer-agent",
        branch="main",
        workflow_run_id=100201
    )
    assert status["workflow_run_id"] == 100201
    assert status["status"] in ("completed", "queued", "in_progress")
    assert status["failed_jobs"] >= 0
    assert len(status["jobs"]) >= 1

@pytest.mark.asyncio
async def test_github_actions_get_failed_jobs():
    failed_jobs = await GitHubActionsToolHandlers.get_failed_jobs(
        workflow_run_id=100201,
        repository="pramod-kumbhar/ai-software-engineer-agent"
    )
    assert len(failed_jobs) >= 1
    assert failed_jobs[0]["conclusion"] == "failure"
    assert "pytest" in failed_jobs[0]["job_name"].lower() or len(failed_jobs[0]["failed_steps"]) > 0

@pytest.mark.asyncio
async def test_github_actions_get_failure_logs_sanitization():
    logs = await GitHubActionsToolHandlers.get_failure_logs(
        workflow_run_id=100201,
        job_id=2002,
        repository="pramod-kumbhar/ai-software-engineer-agent",
        max_chars=5000
    )
    assert logs["job_id"] == 2002
    assert "sanitized_log_excerpt" in logs
    assert len(logs["sanitized_log_excerpt"]) <= 5000
    # Ensure no raw secret tokens remain
    assert "ghp_" not in logs["sanitized_log_excerpt"]

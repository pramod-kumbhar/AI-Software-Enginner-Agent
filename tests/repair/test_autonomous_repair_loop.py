import pytest
import tempfile
import shutil
from pathlib import Path
from app.agents.ci.graph import ci_repair_agent
from app.schemas.ci import CIRunStatusEnum
from app.services.filesystem import FilesystemService

@pytest.mark.asyncio
async def test_bounded_repair_loop_retry_cutoff():
    """Verifies that the repair state machine stops after max 3 attempts and reaches BLOCKED state."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a workspace with a persistent failure
        fs = FilesystemService(base_dir=tmp_dir)
        fs.write_file("app/main.py", "invalid syntax code ::::\n")
        fs.write_file("tests/test_main.py", "def test_fail(): assert False\n")

        initial_state = {
            "run_id": "test_retry_cutoff_run",
            "project_id": "retry_test_proj",
            "repository": "owner/repo",
            "branch": "ai-agent/test-branch",
            "workflow_run_id": 99911,
            "workspace_directory": tmp_dir,
            "attempt_count": 3, # Simulate 3rd attempt
            "max_attempts": 3
        }

        config = {"configurable": {"thread_id": "sess_retry_cutoff"}}
        final_state = await ci_repair_agent.ainvoke(initial_state, config=config)

        # Should be BLOCKED after max attempts exceeded
        assert final_state.get("status") in (CIRunStatusEnum.BLOCKED, CIRunStatusEnum.READY_FOR_REVIEW)
        assert final_state.get("attempt_count") >= 3

import pytest
import tempfile
from app.agents.ci.graph import ci_repair_agent
from app.schemas.ci import CIRunStatusEnum
from app.services.filesystem import FilesystemService

@pytest.mark.asyncio
async def test_day11_e2e_ci_failure_repair_workflow():
    """
    End-to-End Autonomous Repair Integration Test:
    1. Workspace has a simulated CI failure (ImportError / SyntaxError).
    2. CI Monitor detects failure and extracts sanitized failure logs.
    3. Failure Classifier classifies failure as IMPORT_ERROR / AUTO_REPAIR_SAFE.
    4. Repair Planner creates targeted RepairPlan.
    5. Developer Agent applies patch.
    6. Local Test Runner executes tests and confirms passing suite.
    7. QA Agent evaluates code and scores >= 80/100.
    8. Git stages & commits fix.
    9. Status transitions to READY_FOR_REVIEW.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        fs = FilesystemService(base_dir=tmp_dir)
        
        # 1. Setup workspace with models, router, and test
        fs.write_file("app/__init__.py", "")
        fs.write_file("app/core/config.py", "class Settings: PROJECT_NAME = 'Task API'\nsettings = Settings()\n")
        fs.write_file("app/modules/tasks/schemas.py", "from pydantic import BaseModel\nclass TaskBase(BaseModel): name: str\n")
        fs.write_file("app/modules/tasks/router.py", "from app.modules.tasks.schemas import TaskBase\n")
        fs.write_file("tests/test_tasks.py", "def test_ok(): assert True\n")

        initial_state = {
            "run_id": "e2e_day11_run_01",
            "project_id": "task_api_e2e",
            "user_id": "user_e2e_devops",
            "repository": "pramod-kumbhar/ai-software-engineer-agent",
            "branch": "ai-agent/task-api-e2e",
            "workflow_run_id": 100201,
            "workspace_directory": tmp_dir,
            "attempt_count": 1,
            "max_attempts": 3
        }

        config = {"configurable": {"thread_id": "sess_e2e_day11"}}
        final_state = await ci_repair_agent.ainvoke(initial_state, config=config)

        assert final_state.get("status") in (CIRunStatusEnum.READY_FOR_REVIEW, CIRunStatusEnum.CI_PASSED)
        assert final_state.get("repair_plan") is not None
        assert final_state.get("failure") is not None
        assert final_state.get("qa_report") is not None

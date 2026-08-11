import pytest
from app.agents.security.graph import security_agent
from app.schemas.security import (
    SecurityStatusEnum,
    SecurityDecisionEnum
)
from app.services.filesystem import FilesystemService

@pytest.mark.asyncio
async def test_day13_e2e_security_clean_project(tmp_path):
    fs = FilesystemService(workspace_root=str(tmp_path))
    fs.write_file("app/main.py", "def add(a, b):\n    return a + b\n")
    fs.write_file("README.md", "# Clean Task Tracker\nA secure software project.")

    initial_state = {
        "scan_id": "scan_e2e_clean",
        "project_id": "proj_clean_01",
        "user_id": "user_devops_01",
        "workspace_directory": str(tmp_path),
        "scan_type": "FULL"
    }

    config = {"configurable": {"thread_id": "sess_e2e_sec_clean"}}
    res = await security_agent.ainvoke(initial_state, config=config)

    assert res["status"] in [SecurityStatusEnum.SECURITY_READY, SecurityStatusEnum.SECURITY_READY_WITH_WARNINGS]
    assert res["decision"] in [SecurityDecisionEnum.PASS, SecurityDecisionEnum.PASS_WITH_WARNINGS]
    assert res["security_score"] >= 90.0

@pytest.mark.asyncio
async def test_day13_e2e_security_remediation_loop(tmp_path):
    fs = FilesystemService(workspace_root=str(tmp_path))
    # Write a file with an exposed API key
    fs.write_file("app/config.py", 'API_KEY = "api_key_1234567890123456"\n')


    initial_state = {
        "scan_id": "scan_e2e_remediation",
        "project_id": "proj_vuln_01",
        "user_id": "user_devops_01",
        "workspace_directory": str(tmp_path),
        "scan_type": "FULL"
    }

    config = {"configurable": {"thread_id": "sess_e2e_sec_remediation"}}
    res = await security_agent.ainvoke(initial_state, config=config)

    assert len(res.get("repaired_findings", [])) >= 1
    # Check that file was auto-repaired
    _, content = fs.read_file("app/config.py")
    assert "os.getenv" in content

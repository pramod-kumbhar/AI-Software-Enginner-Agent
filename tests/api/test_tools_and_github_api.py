from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_tools_api_lifecycle():
    # 1. List tools
    list_resp = client.get("/api/v1/tools?role=DEVELOPER")
    assert list_resp.status_code == 200
    tools = list_resp.json()
    assert len(tools) >= 10
    
    # 2. Execute safe tool via API
    exec_resp = client.post("/api/v1/tools/execute", json={
        "request_id": "api_tool_req_01",
        "tool_name": "filesystem.list_files",
        "arguments": {"directory": ""},
        "authorization_context": {
            "agent_name": "DeveloperAgent",
            "role": "DEVELOPER",
            "user_id": "test_user",
            "project_id": "test_proj"
        }
    })
    assert exec_resp.status_code == 200
    assert exec_resp.json()["status"] == "SUCCESS"
    
    # 3. Request dangerous tool requiring approval
    commit_resp = client.post("/api/v1/tools/execute", json={
        "request_id": "api_tool_req_commit_01",
        "tool_name": "git.commit",
        "arguments": {"message": "Pending commit"},
        "authorization_context": {
            "agent_name": "DeveloperAgent",
            "role": "DEVELOPER"
        }
    })
    assert commit_resp.status_code == 200
    assert commit_resp.json()["status"] == "PENDING"
    
    # 4. Approve dangerous tool
    approve_resp = client.post("/api/v1/tools/api_tool_req_commit_01/approve", params={"reviewer_name": "TechLead"})
    assert approve_resp.status_code == 200
    assert approve_resp.json()["status"] == "SUCCESS"

def test_github_api_lifecycle():
    # 1. Get repository metadata
    repo_resp = client.get("/api/v1/github/pramod-kumbhar/ai-software-engineer-agent")
    assert repo_resp.status_code == 200
    assert repo_resp.json()["owner"] == "pramod-kumbhar"
    
    # 2. Create Pull Request
    pr_resp = client.post("/api/v1/github/pramod-kumbhar/ai-software-engineer-agent/pull-requests", json={
        "title": "Day 10: MCP Tool Layer & GitHub Integration",
        "body": "Autonomous implementation with full Pytest validation.",
        "head_branch": "ai-agent/day-10-tools",
        "base_branch": "main",
        "approval_confirmed": True,
        "reviewer_name": "Lead_Architect"
    })
    assert pr_resp.status_code == 200
    pr_data = pr_resp.json()
    assert pr_data["pr_number"] > 0

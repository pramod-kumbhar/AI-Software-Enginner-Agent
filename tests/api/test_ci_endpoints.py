import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_ci_monitor_endpoint_lifecycle(client):
    req_body = {
        "user_id": "user_devops_01",
        "project_id": "test_ci_proj_01",
        "repository": "pramod-kumbhar/ai-software-engineer-agent",
        "branch": "ai-agent/task-ci-test",
        "workflow_run_id": 100201
    }
    
    # 1. Trigger Monitor
    resp = client.post("/api/v1/ci/monitor", json=req_body)
    assert resp.status_code == 200
    data = resp.json()
    assert "run_id" in data
    assert data["workflow_run_id"] == 100201
    assert "status" in data
    run_id = data["run_id"]
    
    # 2. Get CI Run
    get_resp = client.get(f"/api/v1/ci/{run_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["run_id"] == run_id
    
    # 3. Get Failures
    fail_resp = client.get(f"/api/v1/ci/{run_id}/failures")
    assert fail_resp.status_code == 200
    assert "failures" in fail_resp.json()
    
    # 4. Approve Repair
    app_resp = client.post(f"/api/v1/ci/{run_id}/approve", json={"reviewer_name": "Lead_DevOps", "notes": "Approved"})
    assert app_resp.status_code == 200
    assert app_resp.json()["status"] == "REPAIRING"

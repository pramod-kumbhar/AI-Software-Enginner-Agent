import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_agent_execute_and_state():
    # 1. Execute agent
    response = client.post(
        "/api/v1/agent/execute",
        json={"prompt": "Build an online bookstore API", "project_id": "proj_api_bookstore", "user_id": "user_api_01"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "execution_id" in data
    assert data["status"] == "WAITING_FOR_APPROVAL"
    assert data["approval_required"] is True
    exec_id = data["execution_id"]
    appr_id = data["approval_id"]

    # 2. Get status
    res_status = client.get(f"/api/v1/agent/{exec_id}")
    assert res_status.status_code == 200
    assert res_status.json()["execution_id"] == exec_id

    # 3. Get full state
    res_state = client.get(f"/api/v1/agent/{exec_id}/state")
    assert res_state.status_code == 200
    assert "plan" in res_state.json()

    # 4. Get timeline
    res_tl = client.get(f"/api/v1/agent/{exec_id}/timeline")
    assert res_tl.status_code == 200
    assert len(res_tl.json()) >= 3

    # 5. Get approval details
    res_appr = client.get(f"/api/v1/approvals/{appr_id}")
    assert res_appr.status_code == 200
    appr_data = res_appr.json()
    assert appr_data["status"] == "PENDING"
    assert appr_data["required_role"] == "TECH_LEAD"

    # 6. Approve architecture via API
    res_dec = client.post(
        f"/api/v1/approvals/{appr_id}/approve",
        json={
            "decision": "APPROVE",
            "reviewer_id": "tech_lead_dave",
            "reviewer_role": "TECH_LEAD",
            "feedback": "Approved via API",
            "action_hash": appr_data["action_hash"]
        }
    )
    assert res_dec.status_code == 200
    assert res_dec.json()["status"] == "APPROVED"

    # 7. Resume agent execution
    res_resume = client.post(
        f"/api/v1/agent/{exec_id}/resume",
        json={}
    )
    assert res_resume.status_code == 200
    res_data = res_resume.json()
    assert res_data["status"] in ["WAITING_FOR_APPROVAL", "COMPLETED"]

def test_api_list_approvals():
    response = client.get("/api/v1/approvals")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1

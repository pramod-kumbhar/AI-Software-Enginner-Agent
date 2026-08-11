from fastapi.testclient import TestClient
from app.main import app
from app.schemas.plan import StructuredSoftwareDevelopmentPlan, ProjectInformation, RequirementsContainer, FunctionalReq

client = TestClient(app)

def test_architect_api_lifecycle():
    # 1. Create a dummy plan in planner
    plan_payload = {
        "user_id": "user_api_test",
        "project_id": "proj_api_test",
        "raw_requirement": "Build a simple user profile and authentication API with email verification."
    }
    plan_resp = client.post("/api/v1/plans/generate", json=plan_payload)
    assert plan_resp.status_code == 200
    plan_data = plan_resp.json()
    planner_task_id = plan_data["task_id"]
    
    # 2. Trigger Architect API
    arch_payload = {
        "user_id": "user_api_test",
        "project_id": "proj_api_test",
        "planner_task_id": planner_task_id
    }
    arch_resp = client.post("/api/v1/architect/generate", json=arch_payload)
    assert arch_resp.status_code == 200
    arch_data = arch_resp.json()
    arch_task_id = arch_data["architect_task_id"]
    assert arch_data["human_approval"]["status"] == "PENDING"
    
    # 3. Retrieve Architecture
    get_resp = client.get(f"/api/v1/architect/{arch_task_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["architect_task_id"] == arch_task_id
    
    # 4. Approve Architecture
    approve_resp = client.post(f"/api/v1/architect/{arch_task_id}/approve", json={"reviewer_name": "Lead Architect", "notes": "LGTM"})
    assert approve_resp.status_code == 200
    assert approve_resp.json()["human_approval"]["status"] == "APPROVED"

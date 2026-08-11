from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_developer_api_lifecycle():
    # 1. Create plan
    plan_resp = client.post("/api/v1/plans/generate", json={
        "user_id": "user_dev_api",
        "project_id": "proj_dev_api",
        "raw_requirement": "Build a simple notification service with email, SMS, and webhook delivery."
    })
    planner_task_id = plan_resp.json()["task_id"]
    
    # 2. Create architecture
    arch_resp = client.post("/api/v1/architect/generate", json={
        "user_id": "user_dev_api",
        "project_id": "proj_dev_api",
        "planner_task_id": planner_task_id
    })
    arch_task_id = arch_resp.json()["architect_task_id"]
    
    # 3. Approve architecture
    client.post(f"/api/v1/architect/{arch_task_id}/approve", json={"reviewer_name": "Reviewer"})
    
    # 4. Generate implementation
    dev_resp = client.post("/api/v1/developer/generate", json={
        "user_id": "user_dev_api",
        "project_id": "proj_dev_api",
        "architect_task_id": arch_task_id
    })
    assert dev_resp.status_code == 200
    dev_data = dev_resp.json()
    dev_task_id = dev_data["developer_task_id"]
    assert len(dev_data["generated_files"]) > 0
    assert dev_data["human_approval"]["status"] == "PENDING"
    
    # 5. Retrieve Implementation
    get_dev = client.get(f"/api/v1/developer/{dev_task_id}")
    assert get_dev.status_code == 200
    
    # 6. Approve Implementation
    app_resp = client.post(f"/api/v1/developer/{dev_task_id}/approve", json={"reviewer_name": "QA Lead", "notes": "Tests pass"})
    assert app_resp.status_code == 200
    assert app_resp.json()["human_approval"]["status"] == "APPROVED"

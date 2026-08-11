import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_release_api_lifecycle():
    # 1. Create Release
    res = client.post("/api/v1/releases/create", json={
        "user_id": "user_tester_01",
        "project_id": "proj_task_mgr",
        "commit_sha": "abc1234",
        "branch": "main",
        "version": "1.0.0",
        "target_environment": "staging"
    })
    assert res.status_code == 201
    data = res.json()
    rel_id = data["release_id"]
    assert "status" in data

    # 2. Get Release
    res = client.get(f"/api/v1/releases/{rel_id}")
    assert res.status_code == 200

    # 3. Validate Release
    res = client.post(f"/api/v1/releases/{rel_id}/validate")
    assert res.status_code == 200
    val_data = res.json()
    assert val_data["ci_status"] == "PASS"

    # 4. Approve Release
    res = client.post(f"/api/v1/releases/{rel_id}/approve", json={
        "user_id": "lead_devops_01",
        "role": "LEAD_DEVOPS",
        "approved": True,
        "comments": "Approved for production promotion."
    })
    assert res.status_code == 200
    assert res.json()["approval_status"] == "APPROVED"

    # 5. Deploy Staging
    res = client.post(f"/api/v1/releases/{rel_id}/deploy/staging", json={
        "user_id": "lead_devops_01",
        "environment": "staging"
    })
    assert res.status_code == 200

    # 6. Deploy Production
    res = client.post(f"/api/v1/releases/{rel_id}/deploy/production", json={
        "user_id": "lead_devops_01",
        "environment": "production"
    })
    assert res.status_code == 200
    assert res.json()["status"] in ["RELEASED", "HEALTH_CHECKING"]

    # 7. Health Probe
    res = client.get(f"/api/v1/releases/{rel_id}/health")
    assert res.status_code == 200

    # 8. Rollback
    res = client.post(f"/api/v1/releases/{rel_id}/rollback", json={
        "user_id": "lead_devops_01",
        "environment": "production",
        "target_version": "0.9.0",
        "reason": "Simulated test rollback"
    })
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 9. History
    res = client.get(f"/api/v1/releases/{rel_id}/history")
    assert res.status_code == 200
    assert "deployments" in res.json()

def test_root_health_and_metrics_probes():
    res = client.get("/health")
    assert res.status_code == 200
    assert "status" in res.json()

    res = client.get("/health/live")
    assert res.status_code == 200
    assert res.json()["alive"] is True

    res = client.get("/health/ready")
    assert res.status_code == 200
    assert "ready" in res.json()

    res = client.get("/health/dependencies")
    assert res.status_code == 200
    assert "dependencies" in res.json()

    res = client.get("/metrics")
    assert res.status_code == 200
    assert "counters" in res.json()

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_security_scan_api_lifecycle(tmp_path):
    # 1. Trigger Security Scan
    res = client.post("/api/v1/security/scan", json={
        "user_id": "user_sec_01",
        "project_id": "proj_hotel_sec",
        "scan_type": "FULL",
        "workspace_directory": str(tmp_path)
    })
    assert res.status_code == 201
    data = res.json()
    scan_id = data["scan_id"]
    assert "security_score" in data
    assert "decision" in data
    assert "findings" in data

    # 2. Get Scan Metadata
    res = client.get(f"/api/v1/security/{scan_id}")
    assert res.status_code == 200

    # 3. Get Findings
    res = client.get(f"/api/v1/security/{scan_id}/findings")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 4. Human Approval Gate
    res = client.post(f"/api/v1/security/{scan_id}/approve", params={"approver_id": "LeadDevOps_Pramod"})
    assert res.status_code == 200
    assert res.json()["status"] == "APPROVED"

    # 5. Project Summary
    res = client.get("/api/v1/security/project/proj_hotel_sec/summary")
    assert res.status_code == 200
    assert res.json()["compliance_status"] == "COMPLIANT"

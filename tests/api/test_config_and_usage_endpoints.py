import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_config_status():
    response = client.get("/api/v1/config/status")
    assert response.status_code == 200
    data = response.json()
    assert "environment" in data
    assert "configured_providers" in data
    assert isinstance(data["configured_providers"], list)
    assert "security_status" in data

def test_api_config_audit():
    response = client.get("/api/v1/config/audit")
    assert response.status_code == 200
    data = response.json()
    assert "is_compliant" in data
    assert "findings" in data

def test_api_list_providers():
    response = client.get("/api/v1/providers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    provider_names = [p["provider"] for p in data]
    assert "ollama" in provider_names or "mock" in provider_names

def test_api_provider_health_mock():
    response = client.get("/api/v1/providers/mock/health")
    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "mock"
    assert data["available"] is True

def test_api_usage_summary():
    response = client.get("/api/v1/usage/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "total_tokens" in data

def test_api_cost_summary():
    response = client.get("/api/v1/cost/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_estimated_cost_usd" in data
    assert data["currency"] == "USD"

def test_api_quota_check():
    response = client.post(
        "/api/v1/quotas/check",
        json={"project_id": "proj_api_test", "estimated_tokens": 500}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["decision"] in ["ALLOWED", "WARNING", "HIGH_USAGE"]

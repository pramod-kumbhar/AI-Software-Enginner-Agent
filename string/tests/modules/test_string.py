import pytest
from app.modules.string.service import stringService
from app.modules.string.schemas import stringCreate

def test_string_service_crud():
    service = stringService()
    created = service.create(stringCreate(name="Test Item", status="ACTIVE"))
    assert created.id is not None
    assert created.name == "Test Item"
    
    fetched = service.get_by_id(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    
    assert len(service.list_all()) == 1
    assert service.delete(created.id) is True
    assert service.get_by_id(created.id) is None

def test_string_api_routes(client):
    # Create
    resp = client.post("/api/v1/string", json={"name": "API Test", "status": "ACTIVE"})
    assert resp.status_code == 201
    data = resp.json()
    record_id = data["id"]
    
    # List
    list_resp = client.get("/api/v1/string")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1
    
    # Get by ID
    get_resp = client.get(f"/api/v1/string/{record_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "API Test"
    
    # 404 on non-existent
    not_found = client.get("/api/v1/string/non_existent_id")
    assert not_found.status_code == 404

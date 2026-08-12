import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_list_evaluation_datasets():
    response = client.get("/api/v1/evaluation-datasets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    dataset_ids = [d["dataset_id"] for d in data]
    assert "benchmark-v1" in dataset_ids
    assert "security-adversarial-v1" in dataset_ids

def test_api_get_dataset_cases():
    response = client.get("/api/v1/evaluation-datasets/benchmark-v1/cases")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) >= 30
    assert cases[0]["case_id"].startswith("case_")

def test_api_run_evaluation_benchmark():
    payload = {
        "dataset_id": "benchmark-v1",
        "model": "llama3:latest",
        "provider": "ollama",
        "project_id": "proj_api_eval_test"
    }
    response = client.post("/api/v1/evaluations/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["evaluation_id"].startswith("eval_")
    assert data["status"] == "PASSED"
    assert data["overall_score"] >= 85.0
    eval_id = data["evaluation_id"]

    # 1. Get Evaluation Details
    res_details = client.get(f"/api/v1/evaluations/{eval_id}")
    assert res_details.status_code == 200
    assert res_details.json()["evaluation_id"] == eval_id

    # 2. Get Evaluation Case Results
    res_results = client.get(f"/api/v1/evaluations/{eval_id}/results")
    assert res_results.status_code == 200
    assert len(res_results.json()) >= 30

    # 3. Get Markdown Report
    res_report = client.get(f"/api/v1/evaluations/{eval_id}/report?format=markdown")
    assert res_report.status_code == 200
    assert "AI Software Engineer Agent Evaluation Report" in res_report.text

    # 4. Submit Human Review
    human_payload = {
        "human_eval_id": "heval_001",
        "evaluation_id": eval_id,
        "reviewer_id": "tech_lead_alice",
        "reviewer_role": "TECH_LEAD",
        "understanding_score": 95.0,
        "architecture_score": 92.0,
        "code_quality_score": 90.0,
        "maintainability_score": 94.0,
        "documentation_score": 92.0,
        "developer_experience_score": 96.0,
        "overall_usefulness_score": 95.0,
        "comments": "High quality benchmark run."
    }
    res_human = client.post(f"/api/v1/evaluations/{eval_id}/human-review", json=human_payload)
    assert res_human.status_code == 200

def test_api_leaderboard_and_regressions():
    # Leaderboard
    res_lead = client.get("/api/v1/evaluations/leaderboard?dataset_id=benchmark-v1")
    assert res_lead.status_code == 200
    assert len(res_lead.json()["entries"]) >= 1

    # Regressions
    res_reg = client.get("/api/v1/evaluations/regressions")
    assert res_reg.status_code == 200

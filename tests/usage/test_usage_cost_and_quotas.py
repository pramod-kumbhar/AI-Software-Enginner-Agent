import pytest
from app.services.usage_tracker import usage_tracker
from app.services.cost_calculator import cost_calculator
from app.services.quota_manager import quota_manager
from app.schemas.configuration import QuotaStatusEnum, ModelPricing

def test_cost_calculator_zero_for_local_ollama():
    cost_rec = cost_calculator.calculate_cost(
        provider="ollama",
        model="llama3:latest",
        input_tokens=1000,
        output_tokens=500
    )
    assert cost_rec.estimated_cost == 0.0
    assert cost_rec.currency == "USD"

def test_cost_calculator_dynamic_pricing():
    custom_pricing = ModelPricing(
        provider="custom_cloud",
        model="custom-1",
        input_cost_per_1k=0.01,
        output_cost_per_1k=0.03
    )
    cost_calculator.set_pricing(custom_pricing)
    
    cost_rec = cost_calculator.calculate_cost(
        provider="custom_cloud",
        model="custom-1",
        input_tokens=1000,
        output_tokens=1000
    )
    assert cost_rec.estimated_cost == 0.04

def test_usage_tracker_records_metrics():
    rec = usage_tracker.record_llm_usage(
        provider="mock",
        model="mock-llama-3-8b",
        input_tokens=250,
        output_tokens=150,
        latency_ms=12.5,
        agent="DeveloperAgent",
        project_id="proj_test_finops_01"
    )
    assert rec.total_tokens == 400
    assert rec.status == "SUCCESS"

    project_records = usage_tracker.get_project_usage("proj_test_finops_01")
    assert len(project_records) >= 1

    summary = usage_tracker.get_summary()
    assert summary.total_requests >= 1
    assert summary.total_tokens >= 400

def test_quota_manager_blocks_excessive_request():
    decision = quota_manager.check_request_quota(
        project_id="proj_test_quota_01",
        user_id="user_test_01",
        estimated_input_tokens=10000 # exceeds 6000 limit
    )
    assert decision.decision == QuotaStatusEnum.BLOCKED
    assert "exceeds maximum allowed per request" in decision.message

def test_quota_manager_allows_standard_request():
    decision = quota_manager.check_request_quota(
        project_id="proj_test_quota_clean",
        user_id="user_test_01",
        estimated_input_tokens=500
    )
    assert decision.decision in [QuotaStatusEnum.ALLOWED, QuotaStatusEnum.WARNING, QuotaStatusEnum.HIGH_USAGE]

def test_agent_iteration_limit_enforced():
    ok_1, _ = quota_manager.check_agent_iteration_quota("PlannerAgent", 5)
    assert ok_1 is True

    ok_2, msg_2 = quota_manager.check_agent_iteration_quota("PlannerAgent", 15) # exceeds max 10
    assert ok_2 is False
    assert "maximum iteration limit" in msg_2

def test_repair_attempt_limit_enforced():
    ok_1, _ = quota_manager.check_repair_attempt_quota("find_1", 2)
    assert ok_1 is True

    ok_2, msg_2 = quota_manager.check_repair_attempt_quota("find_1", 5) # exceeds max 3
    assert ok_2 is False
    assert "Maximum repair attempts" in msg_2

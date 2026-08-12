import pytest
from app.core.llm import llm_client
from app.services.usage_tracker import usage_tracker
from app.services.quota_manager import quota_manager
from app.schemas.plan import RecommendedTechStack

@pytest.mark.asyncio
async def test_day14_e2e_llm_execution_tracking_and_quota():
    # 1. Execute LLM structured call through llm_client with mock provider
    llm_client.provider_name = "mock"
    tech_stack = await llm_client.generate_structured(
        prompt="Design tech stack for microservice",
        system_prompt="You are a principal software architect.",
        schema=RecommendedTechStack,
        agent="ArchitectAgent",
        project_id="proj_e2e_day14",
        user_id="user_e2e_01",
        task_id="task_e2e_arch"
    )
    assert isinstance(tech_stack, RecommendedTechStack)

    # 2. Verify token usage was recorded
    records = usage_tracker.get_project_usage("proj_e2e_day14")
    assert len(records) >= 1
    latest = records[-1]
    assert latest.agent == "ArchitectAgent"
    assert latest.total_tokens > 0

    # 3. Verify project cost was calculated
    cost = usage_tracker.get_project_cost("proj_e2e_day14")
    assert cost >= 0.0

    # 4. Verify quota check for the project remains healthy
    quota_dec = quota_manager.check_request_quota("proj_e2e_day14", "user_e2e_01", estimated_input_tokens=200)
    assert quota_dec.decision.value in ["ALLOWED", "WARNING", "HIGH_USAGE"]

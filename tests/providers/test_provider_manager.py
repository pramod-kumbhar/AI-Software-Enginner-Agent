import pytest
from pydantic import BaseModel
from app.core.providers.manager import provider_manager
from app.core.providers.mock_provider import MockLLMProvider
from app.core.providers.ollama_provider import OllamaProvider

class DummySchema(BaseModel):
    name: str = "Test Task"
    score: int = 100

@pytest.mark.asyncio
async def test_mock_provider_structured_generation():
    mock_prov = MockLLMProvider()
    res = await mock_prov.generate_structured(
        prompt="Generate task",
        system_prompt="You are an assistant",
        schema=DummySchema
    )
    assert isinstance(res, DummySchema)
    assert res.score == 100

@pytest.mark.asyncio
async def test_mock_provider_token_counting():
    mock_prov = MockLLMProvider()
    tokens = mock_prov.count_tokens("Hello world from the agent platform!")
    assert tokens > 0

@pytest.mark.asyncio
async def test_provider_manager_list_and_get():
    prov_list = provider_manager.list_configured_providers()
    assert "ollama" in prov_list
    assert "mock" in prov_list

    mock_p = provider_manager.get_provider("mock")
    assert mock_p.provider_name == "mock"

@pytest.mark.asyncio
async def test_provider_health_checks():
    health = await provider_manager.check_provider_health("mock")
    assert health.configured is True
    assert health.available is True
    assert health.error is None

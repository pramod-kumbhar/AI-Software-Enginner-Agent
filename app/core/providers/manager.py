from typing import Dict, List, Optional, Any
from app.core.providers.base import LLMProvider, EmbeddingProvider
from app.core.providers.ollama_provider import OllamaProvider
from app.core.providers.mock_provider import MockLLMProvider, MockEmbeddingProvider
from app.core.providers.cloud_providers import CloudLLMProvider
from app.core.config import settings
from app.schemas.configuration import ProviderHealthResponse, ProviderTypeEnum
from app.core.logging import logger

class ProviderManager:
    """
    Central manager for LLM and Embedding provider lifecycle, selection, health, and fallback.
    Implements local-first principle and zero credential exposure.
    """

    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {}
        self._embedding_providers: Dict[str, EmbeddingProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initializes providers based on active configuration."""
        # 1. Local Free Providers
        self._providers["ollama"] = OllamaProvider(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
            temperature=settings.OLLAMA_TEMPERATURE
        )
        self._providers["mock"] = MockLLMProvider(model="mock-llama-3-8b")
        self._embedding_providers["mock"] = MockEmbeddingProvider()
        self._embedding_providers["local"] = MockEmbeddingProvider()

        # 2. Cloud Providers (Only initialize if API key present)
        if settings.GROQ_API_KEY:
            self._providers["groq"] = CloudLLMProvider(
                name="groq",
                api_key=settings.GROQ_API_KEY,
                default_model="llama-3.3-70b-versatile",
                base_url="https://api.groq.com/openai/v1"
            )
        if settings.OPENAI_API_KEY:
            self._providers["openai"] = CloudLLMProvider(
                name="openai",
                api_key=settings.OPENAI_API_KEY,
                default_model="gpt-4o-mini",
                base_url="https://api.openai.com/v1"
            )
        if settings.ANTHROPIC_API_KEY:
            self._providers["anthropic"] = CloudLLMProvider(
                name="anthropic",
                api_key=settings.ANTHROPIC_API_KEY,
                default_model="claude-3-5-sonnet-20240620",
                base_url="https://api.anthropic.com/v1"
            )
        if settings.GOOGLE_API_KEY:
            self._providers["google"] = CloudLLMProvider(
                name="google",
                api_key=settings.GOOGLE_API_KEY,
                default_model="gemini-1.5-flash",
                base_url="https://generativelanguage.googleapis.com/v1beta"
            )
        if settings.HUGGINGFACE_API_KEY:
            self._providers["huggingface"] = CloudLLMProvider(
                name="huggingface",
                api_key=settings.HUGGINGFACE_API_KEY,
                default_model="meta-llama/Meta-Llama-3-8B-Instruct",
                base_url="https://api-inference.huggingface.co/models"
            )

    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        """
        Retrieves the requested LLM provider or the system default.
        Falls back to 'mock' in test environment or if requested provider is missing.
        """
        target_name = (name or settings.LLM_PROVIDER or "ollama").lower()
        
        # Test environment optimization
        if settings.is_test and target_name not in self._providers:
            return self._providers["mock"]

        if target_name in self._providers:
            return self._providers[target_name]

        # In dev/test fallback to mock if available, otherwise raise error
        if "mock" in self._providers:
            logger.warning(f"Provider '{target_name}' not configured. Falling back to 'mock' provider.")
            return self._providers["mock"]

        raise ValueError(f"LLM Provider '{target_name}' is not configured and no safe fallback exists.")

    def get_embedding_provider(self, name: Optional[str] = None) -> EmbeddingProvider:
        target_name = (name or settings.EMBEDDING_PROVIDER or "local").lower()
        if target_name in self._embedding_providers:
            return self._embedding_providers[target_name]
        return self._embedding_providers["mock"]

    def register_provider(self, provider: LLMProvider) -> None:
        """Allows registering custom or mock providers at runtime."""
        self._providers[provider.provider_name.lower()] = provider

    def list_configured_providers(self) -> List[str]:
        return list(self._providers.keys())

    async def check_all_providers_health(self) -> List[ProviderHealthResponse]:
        """Checks health status across all configured providers."""
        results = []
        for name, provider in self._providers.items():
            health = await provider.health_check()
            results.append(health)
        return results

    async def check_provider_health(self, name: str) -> ProviderHealthResponse:
        target_name = name.lower()
        if target_name not in self._providers:
            return ProviderHealthResponse(
                provider=name,
                configured=False,
                available=False,
                model="unknown",
                error=f"Provider '{name}' is not configured."
            )
        return await self._providers[target_name].health_check()

provider_manager = ProviderManager()

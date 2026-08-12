import time
from typing import Any, Dict, List, Optional, Type, TypeVar, AsyncIterator
from pydantic import BaseModel
from app.core.providers.base import LLMProvider, EmbeddingProvider
from app.schemas.configuration import ProviderHealthResponse

T = TypeVar("T", bound=BaseModel)

class MockLLMProvider(LLMProvider):
    """Deterministic, zero-network, free Mock LLM provider for unit tests and local simulations."""

    def __init__(self, model: str = "mock-gpt-4o-mini", default_responses: Optional[Dict[str, Any]] = None):
        self._model = model
        self._custom_responses = default_responses or {}
        self.call_history: List[Dict[str, Any]] = []

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def default_model(self) -> str:
        return self._model

    def set_mock_response(self, key: str, value: Any) -> None:
        self._custom_responses[key] = value

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return max(1, len(text) // 4)

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self._model,
            "local": True,
            "cost_per_token": 0.0,
            "mock": True
        }

    async def health_check(self) -> ProviderHealthResponse:
        return ProviderHealthResponse(
            provider=self.provider_name,
            configured=True,
            available=True,
            model=self._model,
            latency_ms=0.5
        )

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str,
        schema: Type[T],
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> T:
        self.call_history.append({
            "type": "structured",
            "prompt": prompt,
            "system_prompt": system_prompt,
            "schema": schema.__name__,
            "model": model or self._model
        })

        # Return predefined mock response if registered for this schema
        if schema.__name__ in self._custom_responses:
            val = self._custom_responses[schema.__name__]
            if isinstance(val, schema):
                return val
            return schema.model_validate(val)

        # Fallback: instantiate schema with dummy default fields
        field_defaults = {}
        for f_name, f_info in schema.model_fields.items():
            if f_info.default is not None and str(f_info.default) != "PydanticUndefined":
                field_defaults[f_name] = f_info.default
            elif f_info.default_factory is not None:
                field_defaults[f_name] = f_info.default_factory()
            elif f_info.annotation in [str, Optional[str]]:
                field_defaults[f_name] = f"Mock {f_name}"
            elif f_info.annotation in [int, Optional[int]]:
                field_defaults[f_name] = 1
            elif f_info.annotation in [float, Optional[float]]:
                field_defaults[f_name] = 1.0
            elif f_info.annotation in [bool, Optional[bool]]:
                field_defaults[f_name] = True
            elif getattr(f_info.annotation, "__origin__", None) is list:
                field_defaults[f_name] = []
            elif getattr(f_info.annotation, "__origin__", None) is dict:
                field_defaults[f_name] = {}
            else:
                field_defaults[f_name] = None
                
        try:
            return schema.model_validate(field_defaults)
        except Exception:
            return schema.model_construct(**field_defaults)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> str:
        self.call_history.append({
            "type": "text",
            "prompt": prompt,
            "system_prompt": system_prompt,
            "model": model or self._model
        })
        return f"Mock LLM generated response for prompt: {prompt[:30]}..."

    async def stream_text(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> AsyncIterator[str]:
        words = ["Mock", "LLM", "streaming", "response", "chunk", "for", "testing."]
        for w in words:
            yield w + " "


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic Mock Embedding Provider."""

    @property
    def provider_name(self) -> str:
        return "mock_embedding"

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [[0.1 * i for i in range(16)] for _ in texts]

    async def embed_query(self, text: str) -> List[float]:
        return [0.1 * i for i in range(16)]

    async def health_check(self) -> ProviderHealthResponse:
        return ProviderHealthResponse(
            provider=self.provider_name,
            configured=True,
            available=True,
            model="mock-embed-dim-16",
            latency_ms=0.1
        )

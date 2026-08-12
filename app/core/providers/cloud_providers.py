import time
from typing import Any, Dict, List, Optional, Type, TypeVar, AsyncIterator
import httpx
from pydantic import BaseModel
from app.core.providers.base import LLMProvider
from app.schemas.configuration import ProviderHealthResponse

T = TypeVar("T", bound=BaseModel)

class CloudLLMProvider(LLMProvider):
    """Generic Cloud LLM Provider adapter supporting OpenAI-compatible and REST endpoints."""

    def __init__(
        self,
        name: str,
        api_key: Optional[str],
        default_model: str,
        base_url: str = "https://api.openai.com/v1"
    ):
        self._name = name
        self._api_key = api_key
        self._default_model = default_model
        self._base_url = base_url.rstrip("/")

    @property
    def provider_name(self) -> str:
        return self._name

    @property
    def default_model(self) -> str:
        return self._default_model

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return max(1, len(text) // 4)

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": self._name,
            "model": self._default_model,
            "configured": bool(self._api_key),
            "local": False
        }

    async def health_check(self) -> ProviderHealthResponse:
        if not self._api_key:
            return ProviderHealthResponse(
                provider=self._name,
                configured=False,
                available=False,
                model=self._default_model,
                error="API key not configured."
            )
        start_time = time.time()
        try:
            headers = {"Authorization": f"Bearer {self._api_key}"}
            timeout_cfg = httpx.Timeout(3.0, connect=1.5)
            async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                resp = await client.get(f"{self._base_url}/models", headers=headers)
                latency = round((time.time() - start_time) * 1000, 2)
                if resp.status_code == 200:
                    return ProviderHealthResponse(
                        provider=self._name,
                        configured=True,
                        available=True,
                        model=self._default_model,
                        latency_ms=latency
                    )
                else:
                    return ProviderHealthResponse(
                        provider=self._name,
                        configured=True,
                        available=False,
                        model=self._default_model,
                        latency_ms=latency,
                        error=f"HTTP {resp.status_code}"
                    )
        except Exception as e:
            latency = round((time.time() - start_time) * 1000, 2)
            return ProviderHealthResponse(
                provider=self._name,
                configured=True,
                available=False,
                model=self._default_model,
                latency_ms=latency,
                error=str(e)[:100]
            )

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str,
        schema: Type[T],
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> T:
        if not self._api_key:
            raise RuntimeError(f"Cannot invoke provider '{self._name}': API key not configured.")
        
        import json
        target_model = model or self._default_model
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        full_system = f"{system_prompt}\nYou MUST respond ONLY with a valid JSON object strictly conforming to this JSON Schema:\n{schema_json}"
        
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": full_system},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature if temperature is not None else 0.2,
            "response_format": {"type": "json_object"}
        }
        
        timeout_cfg = httpx.Timeout(60.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout_cfg) as client:
            resp = await client.post(f"{self._base_url}/chat/completions", headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Cloud provider '{self._name}' returned HTTP {resp.status_code}: {resp.text[:200]}")
            
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return schema.model_validate_json(content)

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> str:
        if not self._api_key:
            raise RuntimeError(f"Cannot invoke provider '{self._name}': API key not configured.")
        
        target_model = model or self._default_model
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature if temperature is not None else 0.2
        }

        timeout_cfg = httpx.Timeout(60.0, connect=5.0)
        async with httpx.AsyncClient(timeout=timeout_cfg) as client:
            resp = await client.post(f"{self._base_url}/chat/completions", headers=headers, json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Cloud provider '{self._name}' returned HTTP {resp.status_code}: {resp.text[:200]}")
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def stream_text(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> AsyncIterator[str]:
        if not self._api_key:
            raise RuntimeError(f"Cannot invoke provider '{self._name}': API key not configured.")
        yield f"Streamed chunk from {self._name}"

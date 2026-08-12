import time
import json
import re
from typing import Any, Dict, List, Optional, Type, TypeVar, AsyncIterator
import httpx
from pydantic import BaseModel
from app.core.providers.base import LLMProvider
from app.core.config import settings
from app.schemas.configuration import ProviderHealthResponse
from app.core.logging import logger

T = TypeVar("T", bound=BaseModel)

class OllamaProvider(LLMProvider):
    """Local-first Ollama LLM provider adapter."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ):
        self._base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self._model = model or settings.OLLAMA_MODEL
        self._temperature = temperature if temperature is not None else settings.OLLAMA_TEMPERATURE

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def default_model(self) -> str:
        return self._model

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        # Fast deterministic token estimate: ~4 chars per token for typical code/English
        return max(1, len(text) // 4)

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "provider": self.provider_name,
            "model": self._model,
            "base_url": self._base_url,
            "local": True,
            "cost_per_token": 0.0
        }

    async def health_check(self) -> ProviderHealthResponse:
        start_time = time.time()
        try:
            timeout_cfg = httpx.Timeout(2.0, connect=1.0)
            async with httpx.AsyncClient(timeout=timeout_cfg) as client:
                resp = await client.get(f"{self._base_url}/api/version")
                latency_ms = round((time.time() - start_time) * 1000, 2)
                if resp.status_code == 200:
                    return ProviderHealthResponse(
                        provider=self.provider_name,
                        configured=True,
                        available=True,
                        model=self._model,
                        latency_ms=latency_ms
                    )
                else:
                    return ProviderHealthResponse(
                        provider=self.provider_name,
                        configured=True,
                        available=False,
                        model=self._model,
                        latency_ms=latency_ms,
                        error=f"HTTP {resp.status_code}"
                    )
        except Exception as e:
            latency_ms = round((time.time() - start_time) * 1000, 2)
            return ProviderHealthResponse(
                provider=self.provider_name,
                configured=True,
                available=False,
                model=self._model,
                latency_ms=latency_ms,
                error=f"Unreachable: {str(e)[:100]}"
            )

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str,
        schema: Type[T],
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> T:
        target_model = model or self._model
        temp = temperature if temperature is not None else self._temperature
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": temp}
        }
        
        timeout_cfg = httpx.Timeout(3.0, connect=1.0)
        async with httpx.AsyncClient(timeout=timeout_cfg) as client:
            response = await client.post(f"{self._base_url}/api/chat", json=payload)
            if response.status_code == 200:
                data = response.json()
                content = data.get("message", {}).get("content", "{}")
                parsed_json = self._extract_and_repair_json(content)
                return schema.model_validate(parsed_json)
            else:
                raise RuntimeError(f"Ollama returned HTTP {response.status_code}: {response.text[:200]}")

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> str:
        target_model = model or self._model
        temp = temperature if temperature is not None else self._temperature
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {"temperature": temp}
        }
        timeout_cfg = httpx.Timeout(settings.OLLAMA_REQUEST_TIMEOUT, connect=2.0)
        async with httpx.AsyncClient(timeout=timeout_cfg) as client:
            response = await client.post(f"{self._base_url}/api/chat", json=payload)
            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")
            else:
                raise RuntimeError(f"Ollama returned HTTP {response.status_code}: {response.text[:200]}")

    async def stream_text(
        self,
        prompt: str,
        system_prompt: str = "",
        temperature: Optional[float] = None,
        model: Optional[str] = None
    ) -> AsyncIterator[str]:
        target_model = model or self._model
        temp = temperature if temperature is not None else self._temperature
        payload = {
            "model": target_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": True,
            "options": {"temperature": temp}
        }
        timeout_cfg = httpx.Timeout(settings.OLLAMA_REQUEST_TIMEOUT, connect=2.0)
        async with httpx.AsyncClient(timeout=timeout_cfg) as client:
            async with client.stream("POST", f"{self._base_url}/api/chat", json=payload) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            yield chunk.get("message", {}).get("content", "")
                        except Exception:
                            continue

    def _extract_and_repair_json(self, text: str) -> dict:
        text = text.strip()
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if json_match:
            text = json_match.group(1).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                cleaned = text[start:end+1]
                return json.loads(cleaned)
            raise ValueError(f"Could not extract valid JSON from response: {text[:150]}")

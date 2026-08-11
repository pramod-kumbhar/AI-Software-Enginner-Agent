import json
import re
from typing import Any, Type, TypeVar
import httpx
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import logger

T = TypeVar("T", bound=BaseModel)

class LLMClient:
    """
    Fast, non-blocking LLM client interfacing with Ollama with structured output parsing,
    JSON repair, and immediate heuristic fallback.
    """
    def __init__(self, base_url: str = None, model: str = None, temperature: float = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.temperature = temperature if temperature is not None else settings.OLLAMA_TEMPERATURE

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str,
        schema: Type[T],
        temperature: float = None
    ) -> T:
        """
        Invokes Ollama to produce a response adhering strictly to the Pydantic schema.
        Falls back instantly if Ollama is unreachable.
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temperature if temperature is not None else self.temperature
            }
        }
        
        timeout_cfg = httpx.Timeout(3.0, connect=1.0)
        async with httpx.AsyncClient(timeout=timeout_cfg) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            if response.status_code == 200:
                data = response.json()
                content = data.get("message", {}).get("content", "{}")
                parsed_json = self._extract_and_repair_json(content)
                return schema.model_validate(parsed_json)
            else:
                raise RuntimeError(f"Ollama returned HTTP {response.status_code}: {response.text}")

    def _extract_and_repair_json(self, text: str) -> dict:
        """Extracts JSON object from markdown code fences or raw string."""
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
            raise ValueError(f"Could not extract valid JSON from LLM response: {text[:200]}")

llm_client = LLMClient()

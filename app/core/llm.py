import time
import json
import re
from typing import Any, Optional, Type, TypeVar
import httpx
from pydantic import BaseModel
from app.core.config import settings
from app.core.logging import logger
from app.core.providers.manager import provider_manager
from app.services.usage_tracker import usage_tracker
from app.services.quota_manager import quota_manager
from app.schemas.configuration import QuotaStatusEnum

T = TypeVar("T", bound=BaseModel)

class LLMClient:
    """
    Production-grade LLM client with local-first provider abstraction,
    token usage tracking, cost calculation, quota enforcement, and structured schema parsing.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        provider_name: Optional[str] = None
    ):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.OLLAMA_MODEL
        self.temperature = temperature if temperature is not None else settings.OLLAMA_TEMPERATURE
        self.provider_name = provider_name or settings.LLM_PROVIDER or "ollama"

    async def generate_structured(
        self,
        prompt: str,
        system_prompt: str,
        schema: Type[T],
        temperature: Optional[float] = None,
        agent: str = "PlannerAgent",
        project_id: str = "default_project",
        user_id: str = "default_user",
        task_id: str = "default_task"
    ) -> T:
        """
        Executes structured generation through the configured provider with pre-flight quota checks
        and post-execution token/cost tracking.
        """
        # 1. Pre-flight token estimate & quota check
        provider = provider_manager.get_provider(self.provider_name)
        input_token_est = provider.count_tokens(system_prompt + "\n" + prompt)
        
        quota_dec = quota_manager.check_request_quota(
            project_id=project_id,
            user_id=user_id,
            estimated_input_tokens=input_token_est,
            estimated_cost_usd=0.0
        )
        if quota_dec.decision == QuotaStatusEnum.BLOCKED:
            raise RuntimeError(f"LLM Execution Blocked by Quota Policy: {quota_dec.message}")

        start_time = time.time()
        output_tokens = 100 # default baseline estimate
        status = "SUCCESS"
        
        try:
            # 2. Invoke active provider
            res = await provider.generate_structured(
                prompt=prompt,
                system_prompt=system_prompt,
                schema=schema,
                temperature=temperature if temperature is not None else self.temperature
            )
            # Estimate output tokens from serialized response
            if hasattr(res, "model_dump_json"):
                output_tokens = provider.count_tokens(res.model_dump_json())
            return res
        except Exception as e:
            status = "FAILED"
            logger.warning(f"Provider {provider.provider_name} call encountered error: {str(e)[:120]}")
            raise e
        finally:
            latency_ms = (time.time() - start_time) * 1000.0
            usage_tracker.record_llm_usage(
                provider=provider.provider_name,
                model=provider.default_model,
                input_tokens=input_token_est,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                agent=agent,
                project_id=project_id,
                user_id=user_id,
                task_id=task_id,
                status=status
            )

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

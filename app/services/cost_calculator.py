from typing import Dict, Optional
from datetime import datetime, timezone
from app.schemas.configuration import ModelPricing, CostRecord

class CostCalculator:
    """
    FinOps Cost Calculation Engine.
    Evaluates token pricing per provider and model dynamically without hardcoded constants.
    """

    def __init__(self):
        self._pricing_catalog: Dict[str, ModelPricing] = {}
        self._initialize_default_pricing()

    def _initialize_default_pricing(self) -> None:
        """Initializes standard pricing catalog with zero-cost defaults for local models."""
        defaults = [
            # Local First Models (Zero API cost)
            ModelPricing(provider="ollama", model="llama3:latest", input_cost_per_1k=0.0, output_cost_per_1k=0.0),
            ModelPricing(provider="ollama", model="llama3.1:latest", input_cost_per_1k=0.0, output_cost_per_1k=0.0),
            ModelPricing(provider="ollama", model="mistral:latest", input_cost_per_1k=0.0, output_cost_per_1k=0.0),
            ModelPricing(provider="mock", model="mock-llama-3-8b", input_cost_per_1k=0.0, output_cost_per_1k=0.0),
            ModelPricing(provider="mock", model="mock-gpt-4o-mini", input_cost_per_1k=0.0, output_cost_per_1k=0.0),
            
            # Optional Cloud Providers (Configurable reference prices)
            ModelPricing(provider="groq", model="llama-3.1-70b-versatile", input_cost_per_1k=0.00059, output_cost_per_1k=0.00079),
            ModelPricing(provider="groq", model="llama-3.1-8b-instant", input_cost_per_1k=0.00005, output_cost_per_1k=0.00008),
            ModelPricing(provider="openai", model="gpt-4o-mini", input_cost_per_1k=0.00015, output_cost_per_1k=0.00060),
            ModelPricing(provider="openai", model="gpt-4o", input_cost_per_1k=0.00250, output_cost_per_1k=0.01000),
            ModelPricing(provider="anthropic", model="claude-3-5-sonnet-20240620", input_cost_per_1k=0.00300, output_cost_per_1k=0.01500),
            ModelPricing(provider="google", model="gemini-1.5-flash", input_cost_per_1k=0.000075, output_cost_per_1k=0.00030)
        ]
        for p in defaults:
            self.set_pricing(p)

    def _make_key(self, provider: str, model: str) -> str:
        return f"{provider.lower()}::{model.lower()}"

    def set_pricing(self, pricing: ModelPricing) -> None:
        key = self._make_key(pricing.provider, pricing.model)
        self._pricing_catalog[key] = pricing

    def get_pricing(self, provider: str, model: str) -> ModelPricing:
        key = self._make_key(provider, model)
        if key in self._pricing_catalog:
            return self._pricing_catalog[key]
        
        # Provider-level generic fallback
        for k, v in self._pricing_catalog.items():
            if k.startswith(f"{provider.lower()}::"):
                return v

        # Zero-cost fallback
        return ModelPricing(
            provider=provider,
            model=model,
            input_cost_per_1k=0.0,
            output_cost_per_1k=0.0
        )

    def calculate_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        usage_id: str = "temp_usage"
    ) -> CostRecord:
        """Calculates USD estimated cost for token volume."""
        pricing = self.get_pricing(provider, model)
        
        input_cost = (input_tokens / 1000.0) * pricing.input_cost_per_1k
        output_cost = (output_tokens / 1000.0) * pricing.output_cost_per_1k
        total_estimated = round(input_cost + output_cost, 6)

        return CostRecord(
            cost_id=f"cost_{int(datetime.now(timezone.utc).timestamp()*1000)}",
            usage_id=usage_id,
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=total_estimated,
            currency="USD"
        )

cost_calculator = CostCalculator()

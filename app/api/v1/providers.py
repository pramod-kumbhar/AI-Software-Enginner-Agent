from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from app.core.providers.manager import provider_manager
from app.schemas.configuration import ProviderHealthResponse

router = APIRouter(prefix="/providers", tags=["Provider Management"])

@router.get("", response_model=List[Dict[str, Any]])
async def list_providers():
    """Lists all configured and available LLM and Embedding providers."""
    providers = []
    for name in provider_manager.list_configured_providers():
        prov = provider_manager.get_provider(name)
        providers.append(prov.get_model_info())
    return providers

@router.get("/{provider}/health", response_model=ProviderHealthResponse)
async def check_provider_health(provider: str):
    """Checks the health and availability of a specific provider without leaking credentials."""
    health = await provider_manager.check_provider_health(provider)
    if not health.configured:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' is not configured.")
    return health

@router.post("/{provider}/validate", response_model=Dict[str, Any])
async def validate_provider(provider: str):
    """Validates connectivity and model inference readiness for a provider."""
    health = await provider_manager.check_provider_health(provider)
    return {
        "provider": provider,
        "valid": health.available,
        "model": health.model,
        "latency_ms": health.latency_ms,
        "error": health.error
    }

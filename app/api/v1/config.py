from fastapi import APIRouter
from app.core.config import settings
from app.core.providers.manager import provider_manager
from app.schemas.configuration import ConfigStatusResponse, ConfigAuditResult
from app.services.config_security_scanner import config_security_scanner

router = APIRouter(prefix="/config", tags=["Configuration & Secrets"])

@router.get("/status", response_model=ConfigStatusResponse)
async def get_configuration_status():
    """
    Returns non-sensitive configuration status and active capabilities.
    Guarantees zero secret leakage (no API keys, tokens, or passwords).
    """
    audit = config_security_scanner.audit_configuration()
    security_status = "COMPLIANT" if audit.is_compliant else "NON_COMPLIANT"

    return ConfigStatusResponse(
        environment=settings.APP_ENV,
        app_name=settings.APP_NAME,
        debug=settings.DEBUG,
        version=settings.VERSION,
        configured_providers=provider_manager.list_configured_providers(),
        database_configured=bool(settings.DATABASE_URL or settings.POSTGRES_SERVER),
        redis_configured=bool(settings.REDIS_URL or settings.REDIS_HOST),
        github_configured=bool(settings.GITHUB_TOKEN),
        observability_enabled=bool(settings.LANGSMITH_TRACING),
        security_status=security_status
    )

@router.get("/audit", response_model=ConfigAuditResult)
async def audit_configuration_security():
    """Audits current environment configuration against production security benchmarks."""
    return config_security_scanner.audit_configuration()

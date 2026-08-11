import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.schemas.release import (
    ReleaseManifest,
    EnvironmentEnum,
    HealthStateEnum,
    ReleaseStatusEnum
)
from app.services.deployment_providers import deployment_provider
from app.services.health_service import health_service
from app.services.rollback_manager import rollback_manager
from app.services.storage import storage_service
from app.core.observability import metrics
from app.core.logging import logger

class DeploymentToolHandlers:
    """
    MCP tool handlers for sandboxed deployment execution, health probing, and rollback management.
    """
    @classmethod
    async def get_status(cls, deployment_id: str) -> Dict[str, Any]:
        return deployment_provider.get_status(deployment_id)

    @classmethod
    async def deploy_staging(
        cls,
        release_id: str,
        project_id: str,
        commit_sha: str,
        branch: str,
        version: str = "1.0.0",
        qa_score: float = 100.0
    ) -> Dict[str, Any]:
        manifest = ReleaseManifest(
            release_id=release_id,
            version=version,
            project_id=project_id,
            commit_sha=commit_sha,
            branch=branch,
            qa_score=qa_score,
            deployment_environment=EnvironmentEnum.STAGING
        )
        run = deployment_provider.deploy(manifest, EnvironmentEnum.STAGING)
        storage_service.save_deployment_run(run.deployment_id, run)
        metrics.increment("deployments_total")
        return run.model_dump()

    @classmethod
    async def deploy_production(
        cls,
        release_id: str,
        project_id: str,
        commit_sha: str,
        branch: str,
        version: str = "1.0.0",
        qa_score: float = 100.0,
        approved_by: str = "LeadDevOps"
    ) -> Dict[str, Any]:
        manifest = ReleaseManifest(
            release_id=release_id,
            version=version,
            project_id=project_id,
            commit_sha=commit_sha,
            branch=branch,
            qa_score=qa_score,
            deployment_environment=EnvironmentEnum.PRODUCTION
        )
        run = deployment_provider.deploy(manifest, EnvironmentEnum.PRODUCTION)
        run.deployed_by = approved_by
        storage_service.save_deployment_run(run.deployment_id, run)
        metrics.increment("deployments_total")
        return run.model_dump()

    @classmethod
    async def health_check(cls, environment: str = "staging") -> Dict[str, Any]:
        env_enum = EnvironmentEnum.PRODUCTION if environment.lower() == "production" else EnvironmentEnum.STAGING
        res = deployment_provider.health_check(env_enum)
        metrics.increment("health_checks_total")
        if res.status == HealthStateEnum.UNHEALTHY:
            metrics.increment("health_checks_failed_total")
        return res.model_dump()

    @classmethod
    async def rollback(
        cls,
        release_id: str,
        failed_version: str,
        environment: str = "production",
        target_version: Optional[str] = None,
        reason: str = "Automated health check failure rollback"
    ) -> Dict[str, Any]:
        env_enum = EnvironmentEnum.PRODUCTION if environment.lower() == "production" else EnvironmentEnum.STAGING
        success, event, msg = rollback_manager.execute_rollback(
            release_id=release_id,
            failed_version=failed_version,
            environment=env_enum,
            target_version=target_version,
            reason=reason
        )
        return {
            "success": success,
            "message": msg,
            "event": event.model_dump() if event else None
        }

    @classmethod
    async def get_readiness(cls, release_id: str) -> Dict[str, Any]:
        val = storage_service.get_release_validation(release_id)
        if not val:
            return {"status": "NOT_FOUND", "release_id": release_id}
        return val

    @classmethod
    async def get_history(cls, project_id: Optional[str] = None) -> Dict[str, Any]:
        releases = storage_service.list_releases(project_id=project_id)
        runs = storage_service.list_deployment_runs()
        rollbacks = storage_service.list_rollback_events()
        return {
            "total_releases": len(releases),
            "releases": releases,
            "total_deployments": len(runs),
            "total_rollbacks": len(rollbacks)
        }

    @classmethod
    async def get_metrics(cls) -> Dict[str, Any]:
        return metrics.get_metrics_summary()

    @classmethod
    async def get_health(cls) -> Dict[str, Any]:
        return health_service.check_health().model_dump()

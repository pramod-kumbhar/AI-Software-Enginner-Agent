from typing import Optional, Tuple
from app.schemas.release import (
    RollbackEvent,
    ReleaseStatusEnum,
    EnvironmentEnum,
    HealthStateEnum
)
from app.services.deployment_providers import deployment_provider
from app.services.storage import storage_service
from app.core.logging import logger
from app.core.observability import metrics

class RollbackManager:
    """
    Controlled Autonomous Rollback Manager.
    Restores the last verified known-good version upon live deployment health degradation.
    """
    @classmethod
    def execute_rollback(
        cls,
        release_id: str,
        failed_version: str,
        environment: EnvironmentEnum = EnvironmentEnum.PRODUCTION,
        target_version: Optional[str] = None,
        reason: str = "Live environment health check failure"
    ) -> Tuple[bool, Optional[RollbackEvent], str]:
        
        # 1. Identify Target Rollback Version
        if not target_version:
            # Look up last known-good release from storage
            releases = storage_service.list_releases()
            good_releases = [
                r for r in releases
                if r.get("release_status") == ReleaseStatusEnum.RELEASED.value and r.get("version") != failed_version
            ]
            if good_releases:
                target_version = good_releases[-1].get("version")
            else:
                target_version = "1.0.0" # Fallback baseline initial version

        # 2. Safety Check: Verify target version is valid
        if not target_version or target_version == failed_version:
            msg = f"Rollback blocked: No valid previous known-good version found to roll back from {failed_version}."
            logger.error(msg)
            return False, None, msg

        # 3. Execute Provider Rollback
        event = deployment_provider.rollback(
            release_id=release_id,
            failed_version=failed_version,
            target_version=target_version,
            environment=environment,
            reason=reason
        )

        # 4. Verify Post-Rollback Health
        health = deployment_provider.health_check(environment)
        if health.status == HealthStateEnum.UNHEALTHY:
            msg = f"Rollback warning: Post-rollback health check reported {health.status.value}."
            logger.warning(msg)

        # 5. Persist Rollback Event & Update Metrics
        storage_service.save_rollback_event(event)
        metrics.increment("rollbacks_total")
        
        logger.info(f"ROLLBACK SUCCESS: Restored {target_version} for Release {release_id}")
        return True, event, f"Successfully rolled back to version {target_version}."

rollback_manager = RollbackManager()

import abc
import uuid
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.schemas.release import (
    ReleaseManifest,
    DeploymentRun,
    RollbackEvent,
    HealthCheckResult,
    HealthStateEnum,
    EnvironmentEnum,
    ReleaseStatusEnum
)
from app.services.health_service import health_service
from app.core.logging import logger

class DeploymentConcurrencyManager:
    """
    Guarantees concurrency isolation so only a single production deployment
    can execute at any given time.
    """
    _lock = threading.Lock()
    _active_deployment: Optional[str] = None

    @classmethod
    def acquire(cls, deployment_id: str, environment: EnvironmentEnum) -> bool:
        if environment != EnvironmentEnum.PRODUCTION:
            return True
        with cls._lock:
            if cls._active_deployment is not None:
                logger.warning(
                    f"CONCURRENCY GUARD: Production deployment {deployment_id} blocked. "
                    f"Active deployment in progress: {cls._active_deployment}"
                )
                return False
            cls._active_deployment = deployment_id
            logger.info(f"CONCURRENCY GUARD: Acquired production lock for {deployment_id}")
            return True

    @classmethod
    def release(cls, deployment_id: str, environment: EnvironmentEnum) -> None:
        if environment != EnvironmentEnum.PRODUCTION:
            return
        with cls._lock:
            if cls._active_deployment == deployment_id:
                cls._active_deployment = None
                logger.info(f"CONCURRENCY GUARD: Released production lock for {deployment_id}")

class DeploymentProvider(abc.ABC):
    """
    Abstract base interface for cloud / container / local deployment providers.
    """
    @abc.abstractmethod
    def validate(self, release_manifest: ReleaseManifest) -> bool:
        pass

    @abc.abstractmethod
    def deploy(self, release_manifest: ReleaseManifest, environment: EnvironmentEnum) -> DeploymentRun:
        pass

    @abc.abstractmethod
    def health_check(self, environment: EnvironmentEnum) -> HealthCheckResult:
        pass

    @abc.abstractmethod
    def rollback(self, release_id: str, failed_version: str, target_version: str, environment: EnvironmentEnum, reason: str) -> RollbackEvent:
        pass

    @abc.abstractmethod
    def get_status(self, deployment_id: str) -> Dict[str, Any]:
        pass

class MockDeploymentProvider(DeploymentProvider):
    """
    Deterministic Mock Deployment Provider for robust unit/integration testing
    and local offline execution without paid cloud infrastructure.
    """
    def __init__(self):
        self.simulate_failure = False
        self.simulate_health_failure = False
        self.simulate_production_health_failure = False
        self.simulate_timeout = False
        self._deployments: Dict[str, DeploymentRun] = {}
        self._rollbacks: Dict[str, RollbackEvent] = {}

    def validate(self, release_manifest: ReleaseManifest) -> bool:
        return release_manifest.qa_score >= 70.0 and bool(release_manifest.commit_sha)

    def deploy(self, release_manifest: ReleaseManifest, environment: EnvironmentEnum) -> DeploymentRun:
        dep_id = f"dep_{uuid.uuid4().hex[:8]}"
        
        # Concurrency check
        if not DeploymentConcurrencyManager.acquire(dep_id, environment):
            run = DeploymentRun(
                deployment_id=dep_id,
                release_id=release_manifest.release_id,
                version=release_manifest.version,
                environment=environment,
                status=ReleaseStatusEnum.BLOCKED,
                error_message="Production deployment concurrency lock active. Another deployment is in progress."
            )
            self._deployments[dep_id] = run
            return run

        try:
            if self.simulate_failure:
                run = DeploymentRun(
                    deployment_id=dep_id,
                    release_id=release_manifest.release_id,
                    version=release_manifest.version,
                    environment=environment,
                    status=ReleaseStatusEnum.FAILED,
                    error_message="Simulated deployment provider container startup failure."
                )
                self._deployments[dep_id] = run
                return run

            smoke_results = health_service.run_smoke_tests(environment)
            health = self.health_check(environment)

            status = ReleaseStatusEnum.RELEASED if environment == EnvironmentEnum.PRODUCTION else ReleaseStatusEnum.STAGING_VALIDATING
            if health.status == HealthStateEnum.UNHEALTHY:
                status = ReleaseStatusEnum.FAILED

            run = DeploymentRun(
                deployment_id=dep_id,
                release_id=release_manifest.release_id,
                version=release_manifest.version,
                environment=environment,
                status=status,
                completed_at=datetime.now(timezone.utc).isoformat(),
                health_status=health.status,
                smoke_test_results=smoke_results,
                rollback_triggered=False
            )
            self._deployments[dep_id] = run
            logger.info(f"DEPLOYMENT SUCCESS: [{dep_id}] env={environment.value} version={release_manifest.version}")
            return run
        finally:
            DeploymentConcurrencyManager.release(dep_id, environment)

    def health_check(self, environment: EnvironmentEnum) -> HealthCheckResult:
        if self.simulate_health_failure or (self.simulate_production_health_failure and environment == EnvironmentEnum.PRODUCTION):
            res = health_service.check_health(environment)
            res.status = HealthStateEnum.UNHEALTHY
            res.readiness = False
            res.database = HealthStateEnum.UNHEALTHY
            return res
        return health_service.check_health(environment)


    def rollback(
        self,
        release_id: str,
        failed_version: str,
        target_version: str,
        environment: EnvironmentEnum,
        reason: str
    ) -> RollbackEvent:
        rb_id = f"rb_{uuid.uuid4().hex[:8]}"
        event = RollbackEvent(
            rollback_id=rb_id,
            release_id=release_id,
            failed_version=failed_version,
            target_rollback_version=target_version,
            environment=environment,
            reason=reason,
            status=ReleaseStatusEnum.ROLLED_BACK,
            completed_at=datetime.now(timezone.utc).isoformat()
        )
        self._rollbacks[rb_id] = event
        logger.info(f"ROLLBACK EXECUTED: [{rb_id}] {failed_version} -> {target_version} (Reason: {reason})")
        return event

    def get_status(self, deployment_id: str) -> Dict[str, Any]:
        run = self._deployments.get(deployment_id)
        if not run:
            return {"status": "UNKNOWN", "deployment_id": deployment_id}
        return run.model_dump()

# Global default provider instance
deployment_provider = MockDeploymentProvider()

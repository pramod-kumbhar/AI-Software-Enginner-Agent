from app.schemas.release import (
    ReleaseManifest,
    EnvironmentEnum,
    ReleaseStatusEnum
)
from app.services.deployment_providers import (
    MockDeploymentProvider,
    DeploymentConcurrencyManager
)

def test_mock_deployment_provider_staging_lifecycle():
    provider = MockDeploymentProvider()
    manifest = ReleaseManifest(
        release_id="rel_dep_01",
        version="1.0.0",
        project_id="proj_hotel",
        commit_sha="a1b2c3d",
        branch="main",
        deployment_environment=EnvironmentEnum.STAGING
    )
    
    # 1. Validate
    assert provider.validate(manifest) is True
    
    # 2. Deploy
    run = provider.deploy(manifest, EnvironmentEnum.STAGING)
    assert run.environment == EnvironmentEnum.STAGING
    assert run.status == ReleaseStatusEnum.STAGING_VALIDATING
    assert len(run.smoke_test_results) == 4

def test_production_deployment_concurrency_lock():
    provider = MockDeploymentProvider()
    manifest = ReleaseManifest(
        release_id="rel_dep_02",
        version="1.0.0",
        project_id="proj_hotel",
        commit_sha="a1b2c3d",
        branch="main",
        deployment_environment=EnvironmentEnum.PRODUCTION
    )

    # Acquire lock manually to simulate in-flight production deployment
    acquired = DeploymentConcurrencyManager.acquire("in_flight_dep_01", EnvironmentEnum.PRODUCTION)
    assert acquired is True

    # Second deployment attempt must be blocked by concurrency guard
    blocked_run = provider.deploy(manifest, EnvironmentEnum.PRODUCTION)
    assert blocked_run.status == ReleaseStatusEnum.BLOCKED
    assert "concurrency lock" in blocked_run.error_message.lower()

    # Release lock
    DeploymentConcurrencyManager.release("in_flight_dep_01", EnvironmentEnum.PRODUCTION)

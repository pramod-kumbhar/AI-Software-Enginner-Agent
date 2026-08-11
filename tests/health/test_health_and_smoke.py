from app.schemas.release import HealthStateEnum, EnvironmentEnum
from app.services.health_service import health_service

def test_health_check_service_probes():
    res = health_service.check_health(EnvironmentEnum.STAGING)
    assert res.status in [HealthStateEnum.HEALTHY, HealthStateEnum.DEGRADED]
    assert res.liveness is True
    assert res.readiness is True
    assert "auth_provider" in res.dependencies
    assert "database_pool" in res.dependencies

def test_smoke_tests_execution():
    results = health_service.run_smoke_tests(EnvironmentEnum.STAGING)
    assert len(results) >= 4
    assert all(r.passed for r in results)

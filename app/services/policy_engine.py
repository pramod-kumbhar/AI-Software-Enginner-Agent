from typing import List, Tuple
from app.core.config import settings
from app.core.logging import logger
from app.schemas.release import (
    ReleaseReadiness,
    ReleaseDecisionEnum,
    ReleaseStatusEnum,
    EnvironmentEnum,
    HealthStateEnum
)

class ReleasePolicyEngine:
    """
    Deterministic Release Policy Engine.
    Evaluates hard policy guardrails to decide whether a release is DEPLOY, DEPLOY_WITH_APPROVAL, BLOCK, or ROLLBACK.
    """
    @classmethod
    def evaluate(cls, readiness: ReleaseReadiness, target_environment: EnvironmentEnum = EnvironmentEnum.STAGING) -> Tuple[ReleaseDecisionEnum, List[str], List[str]]:
        blockers: List[str] = []
        warnings: List[str] = []

        # 1. CI Status Check
        if readiness.ci_status.upper() != "PASS":
            blockers.append(f"CI pipeline validation failed (Status: {readiness.ci_status}).")

        # 2. QA Status & Score Check
        if readiness.qa_status.upper() != "PASS" or readiness.qa_score < settings.RELEASE_MIN_QA_SCORE:
            blockers.append(
                f"QA validation failed or score below threshold: {readiness.qa_score:.1f} < {settings.RELEASE_MIN_QA_SCORE:.1f}"
            )

        # 3. Security Status Check
        if readiness.security_status.upper() != "PASS":
            blockers.append(f"Security scan detected blocking vulnerabilities (Status: {readiness.security_status}).")

        # 4. Architecture Compliance Check
        if readiness.architecture_status.upper() != "PASS":
            blockers.append(f"Architecture validation failed compliance check (Status: {readiness.architecture_status}).")

        # 5. Test Coverage Check
        if readiness.test_coverage < settings.RELEASE_MIN_COVERAGE:
            warnings.append(
                f"Test coverage ({readiness.test_coverage:.1f}%) is below recommended threshold ({settings.RELEASE_MIN_COVERAGE:.1f}%)."
            )

        # 6. Artifact Integrity Check
        if readiness.artifact_status.upper() != "PASS":
            blockers.append("Deployment build artifact is missing, unbuilt, or corrupted.")

        # 7. Environment Direct Deployment Guard
        if target_environment == EnvironmentEnum.PRODUCTION:
            if not settings.PRODUCTION_DEPLOYMENT_ENABLED:
                blockers.append("Production deployment is globally disabled by platform configuration.")
            
            # Direct development -> production is strictly blocked
            if readiness.branch.lower() in ["development", "dev"]:
                blockers.append("Direct promotion from development branch to production is strictly blocked. Must validate in staging first.")

            # Staging Health Check Gate
            if readiness.health_check_status == HealthStateEnum.UNHEALTHY:
                blockers.append("Staging environment health check failed. Promotion to production is blocked.")


        # 8. Determine Final Policy Decision
        if blockers:
            decision = ReleaseDecisionEnum.BLOCK
            logger.warning(f"RELEASE POLICY: BLOCKED for Release {readiness.release_id}. Blockers: {blockers}")
        elif target_environment == EnvironmentEnum.PRODUCTION or settings.RELEASE_REQUIRE_HUMAN_APPROVAL:
            decision = ReleaseDecisionEnum.DEPLOY_WITH_APPROVAL
            logger.info(f"RELEASE POLICY: DEPLOY_WITH_APPROVAL for Release {readiness.release_id} (Target: {target_environment.value})")
        else:
            decision = ReleaseDecisionEnum.DEPLOY
            logger.info(f"RELEASE POLICY: DEPLOY for Release {readiness.release_id} (Target: {target_environment.value})")

        return decision, blockers, warnings

policy_engine = ReleasePolicyEngine()

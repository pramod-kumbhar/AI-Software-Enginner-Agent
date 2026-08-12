from typing import List
from datetime import datetime, timezone
from app.core.config import settings
from app.schemas.configuration import ConfigAuditFinding, ConfigAuditResult
from app.core.logging import logger

class ConfigurationSecurityScanner:
    """
    Security Configuration & Environment Hygiene Auditor.
    Audits active settings against security benchmarks and enforces fail-fast production startup validation.
    """

    @classmethod
    def audit_configuration(cls) -> ConfigAuditResult:
        """Runs a comprehensive security audit on active settings."""
        findings: List[ConfigAuditFinding] = []
        is_prod = settings.is_production

        # 1. Check DEBUG flag in production
        if is_prod and settings.DEBUG:
            findings.append(ConfigAuditFinding(
                rule_id="CONF-01-DEBUG-MODE",
                severity="CRITICAL",
                title="Debug Mode Enabled in Production",
                description="DEBUG is set to True in a production environment, exposing internal traces and endpoints.",
                remediation="Set DEBUG=False in production environment."
            ))

        # 2. Check JWT Secret strength and presence
        if not settings.JWT_SECRET:
            severity = "CRITICAL" if is_prod else "LOW"
            findings.append(ConfigAuditFinding(
                rule_id="CONF-02-MISSING-JWT-SECRET",
                severity=severity,
                title="Missing JWT Secret Key",
                description="JWT_SECRET is unset or empty, weakening token verification.",
                remediation="Set a cryptographically secure JWT_SECRET (>= 32 bytes) in environment variables."
            ))
        elif len(settings.JWT_SECRET) < 32:
            severity = "HIGH" if is_prod else "LOW"
            findings.append(ConfigAuditFinding(
                rule_id="CONF-02-WEAK-JWT-SECRET",
                severity=severity,
                title="Weak JWT Secret Key",
                description="JWT_SECRET is shorter than 32 characters, making it vulnerable to brute force.",
                remediation="Generate a secure random secret of at least 32 characters."
            ))

        # 3. Check Database configuration in production
        if is_prod:
            if not settings.DATABASE_URL and not settings.POSTGRES_PASSWORD:
                findings.append(ConfigAuditFinding(
                    rule_id="CONF-03-UNPROTECTED-DATABASE",
                    severity="CRITICAL",
                    title="Missing Production Database Credentials",
                    description="DATABASE_URL or POSTGRES_PASSWORD is empty in production environment.",
                    remediation="Configure DATABASE_URL with authenticated credentials via environment variables."
                ))

        # 4. Check CORS Policy in production
        if is_prod and ("*" in settings.ALLOWED_CORS_ORIGINS or len(settings.ALLOWED_CORS_ORIGINS) == 0):
            findings.append(ConfigAuditFinding(
                rule_id="CONF-04-WILDCARD-CORS",
                severity="HIGH",
                title="Wildcard CORS Allowed in Production",
                description="ALLOWED_CORS_ORIGINS contains wildcard '*' in production, exposing APIs to cross-origin abuse.",
                remediation="Specify explicit allowed origins (e.g. https://app.example.com)."
            ))

        # 5. Check Production Deployment Approval Gate
        if settings.PRODUCTION_DEPLOYMENT_ENABLED and not settings.RELEASE_REQUIRE_HUMAN_APPROVAL:
            findings.append(ConfigAuditFinding(
                rule_id="CONF-05-AUTONOMOUS-PROD-DEPLOY",
                severity="CRITICAL",
                title="Production Deployment without Human Approval",
                description="PRODUCTION_DEPLOYMENT_ENABLED is True while RELEASE_REQUIRE_HUMAN_APPROVAL is False.",
                remediation="Set RELEASE_REQUIRE_HUMAN_APPROVAL=True to enforce dual-custody release gates."
            ))

        # 6. Check Agent Loop & Token Bounds
        if settings.MAX_AGENT_ITERATIONS > 50:
            findings.append(ConfigAuditFinding(
                rule_id="CONF-06-UNBOUNDED-ITERATIONS",
                severity="HIGH",
                title="Unbounded Agent Iteration Limit",
                description=f"MAX_AGENT_ITERATIONS ({settings.MAX_AGENT_ITERATIONS}) exceeds safe threshold (50).",
                remediation="Configure MAX_AGENT_ITERATIONS to <= 20."
            ))

        if settings.MAX_PROJECT_TOKENS_PER_DAY > 500000:
            findings.append(ConfigAuditFinding(
                rule_id="CONF-07-EXCESSIVE-DAILY-TOKENS",
                severity="MEDIUM",
                title="Excessive Daily Token Quota",
                description=f"MAX_PROJECT_TOKENS_PER_DAY ({settings.MAX_PROJECT_TOKENS_PER_DAY}) is unusually high.",
                remediation="Set a conservative token ceiling to prevent accidental cost spikes."
            ))

        is_compliant = not any(f.severity == "CRITICAL" for f in findings)
        return ConfigAuditResult(
            is_compliant=is_compliant,
            environment=settings.APP_ENV,
            findings=findings,
            checked_at=datetime.now(timezone.utc).isoformat()
        )

    @classmethod
    def validate_production_startup(cls) -> None:
        """
        Fail-fast check on startup for production environment.
        Raises RuntimeError with safe non-leaking message if critical issues are found.
        """
        if not settings.is_production:
            return

        audit = cls.audit_configuration()
        critical_findings = [f for f in audit.findings if f.severity == "CRITICAL"]
        if critical_findings:
            error_msg = "; ".join([f"{f.title}: {f.description}" for f in critical_findings])
            logger.critical(f"FATAL PRODUCTION CONFIG ERROR: {error_msg}")
            raise RuntimeError(f"Production startup aborted due to configuration security violations: {error_msg}")

config_security_scanner = ConfigurationSecurityScanner()

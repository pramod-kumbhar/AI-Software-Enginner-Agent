from typing import List, Dict, Any, Tuple
from app.schemas.security import (
    SecurityFinding,
    SecuritySeverityEnum,
    SecurityStatusEnum,
    SecurityDecisionEnum,
    SecurityCategoryEnum,
    SecurityRepairPlan
)
from app.core.logger import get_logger

logger = get_logger("security_gate")

class SecurityGate:
    """
    Deterministic Security Gate & 100-Point Scoring Engine.
    Evaluates multi-domain security findings and enforces hard release blocking gates.
    """

    CATEGORY_WEIGHTS: Dict[SecurityCategoryEnum, float] = {
        SecurityCategoryEnum.AUTHENTICATION: 10.0,
        SecurityCategoryEnum.AUTHORIZATION: 10.0,
        SecurityCategoryEnum.SECRETS: 10.0,
        SecurityCategoryEnum.FILESYSTEM: 5.0,
        SecurityCategoryEnum.COMMAND_EXECUTION: 5.0,
        SecurityCategoryEnum.MCP_SECURITY: 10.0,
        SecurityCategoryEnum.GIT_GITHUB: 10.0,
        SecurityCategoryEnum.CI_CD: 10.0,
        SecurityCategoryEnum.DEPENDENCIES: 5.0,
        SecurityCategoryEnum.CODE_SECURITY: 10.0,
        SecurityCategoryEnum.PROMPT_INJECTION: 10.0,
        SecurityCategoryEnum.AUDITABILITY: 5.0,
    }

    SEVERITY_DEDUCTIONS: Dict[SecuritySeverityEnum, float] = {
        SecuritySeverityEnum.CRITICAL: 25.0,
        SecuritySeverityEnum.HIGH: 10.0,
        SecuritySeverityEnum.MEDIUM: 5.0,
        SecuritySeverityEnum.LOW: 1.0,
        SecuritySeverityEnum.INFO: 0.0
    }

    @classmethod
    def evaluate(cls, findings: List[SecurityFinding]) -> Tuple[float, SecurityStatusEnum, SecurityDecisionEnum, List[str]]:
        """
        Calculates security score (0-100), overall status, and deterministic gate decision.
        Returns (score, status, decision, blockers).
        """
        score = 100.0
        blockers: List[str] = []
        
        crit_count = sum(1 for f in findings if f.severity == SecuritySeverityEnum.CRITICAL and f.status == "OPEN")
        high_count = sum(1 for f in findings if f.severity == SecuritySeverityEnum.HIGH and f.status == "OPEN")
        med_count = sum(1 for f in findings if f.severity == SecuritySeverityEnum.MEDIUM and f.status == "OPEN")
        low_count = sum(1 for f in findings if f.severity == SecuritySeverityEnum.LOW and f.status == "OPEN")

        for f in findings:
            if f.status == "OPEN":
                deduction = cls.SEVERITY_DEDUCTIONS.get(f.severity, 0.0)
                score -= deduction
                if f.severity in [SecuritySeverityEnum.CRITICAL, SecuritySeverityEnum.HIGH]:
                    blockers.append(f"[{f.severity.value}] {f.title} (File: {f.file_path or 'N/A'})")

        score = max(0.0, min(100.0, score))

        # Determine Decision and Status
        if crit_count > 0:
            status = SecurityStatusEnum.CRITICAL_SECURITY_BLOCK
            decision = SecurityDecisionEnum.CRITICAL_BLOCK
        elif high_count > 0 or score < 70.0:
            status = SecurityStatusEnum.NEEDS_SECURITY_FIXES
            decision = SecurityDecisionEnum.BLOCK
        elif med_count > 0 or low_count > 0 or score < 90.0:
            status = SecurityStatusEnum.SECURITY_READY_WITH_WARNINGS
            decision = SecurityDecisionEnum.PASS_WITH_WARNINGS
        else:
            status = SecurityStatusEnum.SECURITY_READY
            decision = SecurityDecisionEnum.PASS

        logger.info(
            f"SECURITY GATE EVALUATION: Score={score:.1f}/100 Status={status.value} "
            f"Decision={decision.value} (Crit={crit_count}, High={high_count}, Med={med_count}, Low={low_count})"
        )

        return score, status, decision, blockers

    @classmethod
    def classify_repairability(cls, finding: SecurityFinding) -> Tuple[bool, bool]:
        """
        Classifies whether a finding is safely auto-fixable and whether human approval is required.
        Returns (is_auto_fixable, approval_required).
        """
        # High-risk security modifications strictly require human sign-off
        high_risk_categories = {
            SecurityCategoryEnum.AUTHENTICATION,
            SecurityCategoryEnum.AUTHORIZATION,
            SecurityCategoryEnum.DEPLOYMENT_SECURITY
        }

        if finding.category in high_risk_categories or finding.severity == SecuritySeverityEnum.CRITICAL:
            return False, True

        if finding.category == SecurityCategoryEnum.SECRETS:
            # Masking / moving to env is auto-fixable
            return True, False

        if finding.category in [SecurityCategoryEnum.CODE_SECURITY, SecurityCategoryEnum.DEPENDENCIES]:
            return True, False

        return False, False

security_gate = SecurityGate()

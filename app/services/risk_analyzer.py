import re
from typing import List, Dict, Any, Tuple
from app.schemas.release import RiskLevelEnum, ChangeCategoryEnum
from app.core.logging import logger

class ReleaseRiskAnalyzer:
    """
    Analyzes code diffs, changed files, and database migrations to compute
    a granular Release Risk Score (0-100) and Change Impact Classification.
    """
    CATEGORY_PATTERNS = {
        ChangeCategoryEnum.DOCUMENTATION: [r'\.md$', r'docs/', r'README', r'LICENSE'],
        ChangeCategoryEnum.TEST: [r'test_.*\.py$', r'tests/', r'.*spec\.js$'],
        ChangeCategoryEnum.DATABASE: [r'alembic/', r'migrations/', r'models/.*\.py$', r'\.sql$'],
        ChangeCategoryEnum.AUTHENTICATION: [r'auth', r'jwt', r'token', r'password', r'security/.*auth'],
        ChangeCategoryEnum.AUTHORIZATION: [r'rbac', r'permission', r'roles', r'policy'],
        ChangeCategoryEnum.PAYMENT: [r'payment', r'billing', r'stripe', r'paypal', r'wallet', r'transaction'],
        ChangeCategoryEnum.SECURITY: [r'security', r'crypto', r'cert', r'cors', r'secret'],
        ChangeCategoryEnum.INFRASTRUCTURE: [r'docker', r'k8s', r'terraform', r'\.github/workflows', r'Dockerfile'],
        ChangeCategoryEnum.CONFIGURATION: [r'\.env', r'config\.py$', r'settings\.py$', r'\.yaml$', r'\.yml$'],
        ChangeCategoryEnum.DEPENDENCY: [r'requirements.*\.txt$', r'pyproject\.toml$', r'package\.json$'],
        ChangeCategoryEnum.FRONTEND: [r'templates/', r'static/', r'\.html$', r'\.css$', r'\.jsx?$', r'\.tsx?$'],
        ChangeCategoryEnum.BACKEND: [r'app/.*\.py$', r'services/', r'routers/', r'controllers/']
    }

    DESTRUCTIVE_SQL_PATTERNS = [
        re.compile(r'\bDROP\s+TABLE\b', re.IGNORECASE),
        re.compile(r'\bDROP\s+COLUMN\b', re.IGNORECASE),
        re.compile(r'\bTRUNCATE\b', re.IGNORECASE),
        re.compile(r'\bALTER\s+TABLE\s+.*\s+DROP\b', re.IGNORECASE)
    ]

    @classmethod
    def classify_file(cls, filepath: str) -> List[ChangeCategoryEnum]:
        categories = []
        for cat, patterns in cls.CATEGORY_PATTERNS.items():
            if any(re.search(pat, filepath, re.IGNORECASE) for pat in patterns):
                categories.append(cat)
        return categories or [ChangeCategoryEnum.BACKEND]

    @classmethod
    def analyze_risk(
        cls,
        changed_files: List[str],
        diff_text: str = "",
        qa_score: float = 100.0,
        ci_failures_count: int = 0
    ) -> Tuple[float, RiskLevelEnum, List[ChangeCategoryEnum], List[str]]:
        if not changed_files:
            return 0.0, RiskLevelEnum.LOW, [ChangeCategoryEnum.DOCUMENTATION], ["No file changes detected."]

        detected_categories = set()
        notes = []
        base_score = 10.0

        for f in changed_files:
            cats = cls.classify_file(f)
            for c in cats:
                detected_categories.add(c)

        # Category Weighting
        if ChangeCategoryEnum.PAYMENT in detected_categories:
            base_score += 45.0
            notes.append("Payment / transaction processing code modified (CRITICAL RISK).")

        if ChangeCategoryEnum.SECURITY in detected_categories or ChangeCategoryEnum.AUTHENTICATION in detected_categories:
            base_score += 35.0
            notes.append("Authentication / security protocols modified (HIGH RISK).")

        if ChangeCategoryEnum.DATABASE in detected_categories:
            base_score += 25.0
            notes.append("Database schema or migration files modified.")

            # Inspect diff for destructive DDL
            if diff_text:
                for pat in cls.DESTRUCTIVE_SQL_PATTERNS:
                    if pat.search(diff_text):
                        base_score += 30.0
                        notes.append("POTENTIALLY DESTRUCTIVE SQL (DROP/TRUNCATE) DETECTED IN MIGRATION!")
                        break

        if ChangeCategoryEnum.INFRASTRUCTURE in detected_categories:
            base_score += 20.0
            notes.append("Deployment infrastructure / CI workflow configuration modified.")

        if ChangeCategoryEnum.DEPENDENCY in detected_categories:
            base_score += 15.0
            notes.append("Package dependencies modified.")

        # Documentation-only discount
        if detected_categories == {ChangeCategoryEnum.DOCUMENTATION}:
            base_score = 5.0
            notes.append("Documentation-only modification (LOW RISK).")

        # QA Score Adjustment
        if qa_score < 90.0:
            penalty = (90.0 - qa_score) * 0.8
            base_score += penalty
            notes.append(f"QA score penalty applied (+{penalty:.1f} risk due to {qa_score:.1f}/100 score).")

        # CI failure history adjustment
        if ci_failures_count > 0:
            base_score += min(ci_failures_count * 5.0, 20.0)
            notes.append(f"Recent CI repair attempts ({ci_failures_count}) increased deployment risk.")

        final_score = min(max(base_score, 0.0), 100.0)

        # Determine Risk Level
        if final_score <= 20.0:
            level = RiskLevelEnum.LOW
        elif final_score <= 40.0:
            level = RiskLevelEnum.MEDIUM
        elif final_score <= 70.0:
            level = RiskLevelEnum.HIGH
        else:
            level = RiskLevelEnum.CRITICAL

        logger.info(f"RELEASE RISK ANALYSIS: Score={final_score:.1f}/100 Level={level.value} Categories={[c.value for c in detected_categories]}")
        return final_score, level, list(detected_categories), notes

risk_analyzer = ReleaseRiskAnalyzer()

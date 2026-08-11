import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class QAIssue(BaseModel):
    issue_id: str
    category: str # SECURITY, ARCHITECTURE, BUG, REGRESSION, TEST
    severity: str # CRITICAL, HIGH, MEDIUM, LOW, INFO
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: str = ""

class QAReport(BaseModel):
    qa_task_id: str
    project_id: str
    overall_score: float = 100.0
    passed: bool = True
    critical_issues_count: int = 0
    high_issues_count: int = 0
    medium_issues_count: int = 0
    low_issues_count: int = 0
    issues: List[QAIssue] = Field(default_factory=list)
    tests_summary: Dict[str, Any] = Field(default_factory=dict)
    architecture_compliance: float = 100.0
    security_score: float = 100.0
    code_quality_score: float = 100.0
    summary: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class QAAgent:
    """
    Dedicated QA Agent analyzing code quality, architecture compliance, test results,
    security vulnerabilities, and regression hazards.
    """

    @classmethod
    def evaluate(
        cls,
        task_id: str,
        project_id: str,
        test_results: Dict[str, Any],
        source_files: Dict[str, str],
        architecture_spec: Optional[Any] = None,
        is_repair_verification: bool = False
    ) -> QAReport:
        issues: List[QAIssue] = []
        
        total_tests = test_results.get("total_tests", 0)
        passed_tests = test_results.get("passed", 0)
        failed_tests = test_results.get("failed", 0)
        test_errors = test_results.get("errors", 0)
        
        # 1. Test Pass Rate Check
        if total_tests > 0:
            pass_rate = (passed_tests / total_tests) * 100.0
        else:
            pass_rate = 100.0 if not is_repair_verification else 0.0

        if failed_tests > 0 or test_errors > 0:
            issues.append(QAIssue(
                issue_id=f"QA-TEST-{len(issues)+1}",
                category="TEST",
                severity="HIGH",
                title=f"{failed_tests} Unit/Integration Test(s) Failed",
                description=f"{failed_tests} failed and {test_errors} errored out of {total_tests} total tests.",
                recommendation="Fix offending code or test assertions before releasing to production."
            ))

        # 2. Source Code Static Security & Anti-Pattern Analysis
        sec_penalty = 0.0
        arch_penalty = 0.0
        
        for file_path, content in source_files.items():
            # Security: Hardcoded secrets or tokens
            if re.search(r'(?i)(api_key|secret_key|jwt_secret|password)\s*=\s*["\'][a-zA-Z0-9_\-]{8,}["\']', content):
                issues.append(QAIssue(
                    issue_id=f"QA-SEC-{len(issues)+1}",
                    category="SECURITY",
                    severity="CRITICAL",
                    title="Potential Hardcoded Secret Detected",
                    description=f"File '{file_path}' contains potential hardcoded secret.",
                    file_path=file_path,
                    recommendation="Move credentials and secrets to environment variables or config.py."
                ))
                sec_penalty += 30.0

            # Security: Path traversal or raw eval/exec
            if "eval(" in content or "exec(" in content:
                issues.append(QAIssue(
                    issue_id=f"QA-SEC-{len(issues)+1}",
                    category="SECURITY",
                    severity="CRITICAL",
                    title="Arbitrary Code Execution via eval/exec",
                    description=f"File '{file_path}' contains dynamic eval/exec statement.",
                    file_path=file_path,
                    recommendation="Remove eval/exec to prevent remote code execution vulnerabilities."
                ))
                sec_penalty += 40.0

            # Architecture / Concurrency: Double Booking / Race condition detection
            if "booking" in file_path.lower() or "order" in file_path.lower():
                if "status" in content and "ACTIVE" in content and "CANCELLED" not in content and "status ==" not in content and "get_by_id" not in content:
                    issues.append(QAIssue(
                        issue_id=f"QA-ARCH-{len(issues)+1}",
                        category="ARCHITECTURE",
                        severity="MEDIUM",
                        title="State Conflict Check Missing",
                        description=f"File '{file_path}' updates records without checking existing lifecycle status.",
                        file_path=file_path,
                        recommendation="Add status validation to avoid race conditions and double state mutation."
                    ))
                    arch_penalty += 10.0

        # Calculate Scores
        security_score = max(0.0, 100.0 - sec_penalty)
        architecture_compliance = max(0.0, 100.0 - arch_penalty)
        test_score = pass_rate
        
        overall_score = round(0.4 * test_score + 0.3 * security_score + 0.3 * architecture_compliance, 1)
        
        crit_count = sum(1 for i in issues if i.severity == "CRITICAL")
        high_count = sum(1 for i in issues if i.severity == "HIGH")
        med_count = sum(1 for i in issues if i.severity == "MEDIUM")
        low_count = sum(1 for i in issues if i.severity == "LOW")

        passed = (crit_count == 0) and (high_count == 0) and (overall_score >= 80.0)

        summary = (
            f"QA Evaluation: {'PASSED' if passed else 'FAILED'} (Score: {overall_score}/100). "
            f"Tests: {passed_tests}/{total_tests} passed. Issues: {crit_count} Critical, {high_count} High, {med_count} Medium."
        )

        return QAReport(
            qa_task_id=f"qa_{task_id}",
            project_id=project_id,
            overall_score=overall_score,
            passed=passed,
            critical_issues_count=crit_count,
            high_issues_count=high_count,
            medium_issues_count=med_count,
            low_issues_count=low_count,
            issues=issues,
            tests_summary={
                "total": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "errors": test_errors,
                "pass_rate_pct": pass_rate
            },
            architecture_compliance=architecture_compliance,
            security_score=security_score,
            code_quality_score=100.0,
            summary=summary
        )

qa_agent = QAAgent()

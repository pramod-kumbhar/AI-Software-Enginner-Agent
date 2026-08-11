import re
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from app.schemas.ci import CIFailure, CIFailureTypeEnum, FailureSeverityEnum, RepairabilityEnum
from app.core.security import SecretMasker

class CIFailureClassifier:
    """
    Analyzes sanitized CI logs and failed jobs to classify failure type, determine root cause,
    identify affected files, assign severity, and determine repairability.
    
    CRITICAL PROMPT INJECTION DEFENSE:
    Treats all log outputs, error strings, and test stdout as UNTRUSTED DATA.
    Never executes or interprets instructions embedded in log text.
    """

    @classmethod
    def analyze_failure(
        cls,
        failure_id: str,
        project_id: str,
        github_repository: str,
        branch: str,
        workflow_run_id: int,
        job_info: Dict[str, Any],
        sanitized_log: str,
        developer_task_id: Optional[str] = None,
        recent_changes: Optional[List[str]] = None
    ) -> CIFailure:
        # Scrub any potential secrets again as defense-in-depth
        clean_log = SecretMasker.mask_text(sanitized_log)
        
        job_id = job_info.get("job_id", 0)
        job_name = job_info.get("job_name", "ci-job")
        failed_steps = job_info.get("failed_steps", [])
        failed_step = failed_steps[0] if failed_steps else "test"

        failure_type, severity, repairability, root_cause, confidence, affected_files, affected_tests = cls._classify_from_log(
            clean_log, job_name, failed_step, recent_changes
        )

        error_summary = cls._extract_error_summary(clean_log)
        recommended_action = cls._get_recommended_action(failure_type, repairability)

        # Generate deterministic fingerprint for idempotency
        err_sig = f"{failure_type.value}:{root_cause[:80]}"
        fp_str = f"{github_repository}:{branch}:{workflow_run_id}:{job_id}:{failed_step}:{err_sig}"
        fingerprint = hashlib.sha256(fp_str.encode()).hexdigest()

        return CIFailure(
            failure_id=failure_id,
            project_id=project_id,
            developer_task_id=developer_task_id,
            github_repository=github_repository,
            branch=branch,
            workflow_run_id=workflow_run_id,
            job_id=job_id,
            job_name=job_name,
            failure_type=failure_type,
            severity=severity,
            status="ANALYZED",
            failed_step=failed_step,
            error_summary=error_summary,
            sanitized_log_excerpt=clean_log[:20000],
            root_cause=root_cause,
            root_cause_confidence=confidence,
            affected_files=affected_files,
            affected_tests=affected_tests,
            repairability=repairability,
            recommended_action=recommended_action,
            fingerprint=fingerprint
        )

    @classmethod
    def _classify_from_log(
        cls,
        log: str,
        job_name: str,
        failed_step: str,
        recent_changes: Optional[List[str]] = None
    ) -> Tuple[CIFailureTypeEnum, FailureSeverityEnum, RepairabilityEnum, str, float, List[str], List[str]]:
        affected_files: List[str] = list(recent_changes or [])
        affected_tests: List[str] = []

        # 1. Check for Syntax Errors
        syntax_match = re.search(r'SyntaxError:\s*(.*)', log)
        if syntax_match or "invalid syntax" in log:
            file_match = re.search(r'File "([^"]+)", line (\d+)', log)
            if file_match:
                fpath = file_match.group(1)
                if not fpath.startswith("/usr") and not "site-packages" in fpath:
                    affected_files.append(fpath)
            err_msg = syntax_match.group(1) if syntax_match else "Invalid Python syntax"
            return (
                CIFailureTypeEnum.SYNTAX_ERROR,
                FailureSeverityEnum.HIGH,
                RepairabilityEnum.AUTO_REPAIR_SAFE,
                f"SyntaxError detected: {err_msg}",
                0.95,
                list(set(affected_files)),
                affected_tests
            )

        # 2. Check for Import Errors / Module Not Found
        import_match = re.search(r'(?:ImportError|ModuleNotFoundError):\s*(.*)', log)
        if import_match:
            err_msg = import_match.group(1)
            # Extract affected file from traceback
            file_matches = re.findall(r'File "([^"]+)"', log)
            for f in file_matches:
                if not f.startswith("/usr") and "site-packages" not in f:
                    affected_files.append(f)
            return (
                CIFailureTypeEnum.IMPORT_ERROR,
                FailureSeverityEnum.HIGH,
                RepairabilityEnum.AUTO_REPAIR_SAFE,
                f"Import error: {err_msg}",
                0.95,
                list(set(affected_files)),
                affected_tests
            )

        # 3. Check for Security / Authentication Failure
        if "401 Unauthorized" in log or "403 Forbidden" in log or "JWT validation failed" in log or "Invalid credentials" in log:
            return (
                CIFailureTypeEnum.AUTHENTICATION_FAILURE,
                FailureSeverityEnum.HIGH,
                RepairabilityEnum.AUTO_REPAIR_WITH_APPROVAL,
                "Authentication or authorization credentials validation failure in API request.",
                0.90,
                list(set(affected_files)),
                affected_tests
            )

        # 4. Check for External Network / GitHub / Service Outage
        if "Connection refused" in log or "502 Bad Gateway" in log or "GitHub API 500" in log or "Service Unavailable" in log:
            return (
                CIFailureTypeEnum.NETWORK_FAILURE,
                FailureSeverityEnum.MEDIUM,
                RepairabilityEnum.EXTERNAL_DEPENDENCY,
                "External service or network dependency unavailable during CI execution.",
                0.85,
                list(set(affected_files)),
                affected_tests
            )

        # 5. Check for Lint / Formatting Failures
        if "ruff check" in log or "flake8" in log or "black --check" in log or "lint" in job_name.lower():
            if "error:" in log.lower() or "failed" in log.lower():
                return (
                    CIFailureTypeEnum.LINT_FAILURE,
                    FailureSeverityEnum.LOW,
                    RepairabilityEnum.AUTO_REPAIR_SAFE,
                    "Code formatting or linting violation detected by CI linter.",
                    0.90,
                    list(set(affected_files)),
                    affected_tests
                )

        # 6. Check for Type Check (Mypy) Failure
        if "mypy" in log or "Incompatible types" in log:
            return (
                CIFailureTypeEnum.TYPE_CHECK_FAILURE,
                FailureSeverityEnum.LOW,
                RepairabilityEnum.AUTO_REPAIR_SAFE,
                "Static type checker detected incompatible types or missing signatures.",
                0.90,
                list(set(affected_files)),
                affected_tests
            )

        # 7. Check for Test Failures (AssertionError / HTTP 500 vs 200)
        test_fail_matches = re.findall(r'FAILED (tests/[^:\s]+)(?:::(\w+))?', log)
        for tmatch in test_fail_matches:
            if isinstance(tmatch, tuple):
                tpath = tmatch[0]
                affected_tests.append(tpath)
            else:
                affected_tests.append(tmatch)

        assert_match = re.search(r'AssertionError:\s*(.*)', log)
        diff_match = re.search(r'assert\s+(.*)', log)
        
        if test_fail_matches or assert_match or "FAILED tests/" in log:
            err_reason = assert_match.group(1) if assert_match else (diff_match.group(1) if diff_match else "Test assertion failed")
            
            # Check if business logic or simple bug
            is_business_critical = any(kw in log.lower() for kw in ["payment", "booking_conflict", "auth", "permission", "security"])
            repair_mode = RepairabilityEnum.AUTO_REPAIR_WITH_APPROVAL if is_business_critical else RepairabilityEnum.AUTO_REPAIR_SAFE

            # Extract module files from traceback
            file_matches = re.findall(r'File "([^"]+)"', log)
            for f in file_matches:
                if not f.startswith("/usr") and "site-packages" not in f and not f.startswith("tests/"):
                    affected_files.append(f)

            return (
                CIFailureTypeEnum.TEST_FAILURE,
                FailureSeverityEnum.HIGH,
                repair_mode,
                f"Pytest assertion failure: {err_reason}",
                0.90,
                list(set(affected_files)),
                list(set(affected_tests))
            )

        # 8. Check for Timeout
        if "Timeout" in log or "timed out after" in log:
            return (
                CIFailureTypeEnum.TIMEOUT,
                FailureSeverityEnum.MEDIUM,
                RepairabilityEnum.AUTO_REPAIR_SAFE,
                "Process or test execution timed out exceeding maximum duration.",
                0.80,
                list(set(affected_files)),
                affected_tests
            )

        # Default fallback
        return (
            CIFailureTypeEnum.UNKNOWN,
            FailureSeverityEnum.MEDIUM,
            RepairabilityEnum.AUTO_REPAIR_SAFE,
            "Unclassified failure in step: " + failed_step,
            0.60,
            list(set(affected_files)),
            affected_tests
        )

    @classmethod
    def _extract_error_summary(cls, log: str) -> str:
        for line in log.splitlines():
            line_s = line.strip()
            if any(line_s.startswith(p) for p in ["E   ", "Error:", "FAILED ", "SyntaxError:", "ImportError:"]):
                return line_s[:200]
        return "CI job completed with failure exit code."

    @classmethod
    def _get_recommended_action(cls, failure_type: CIFailureTypeEnum, repairability: RepairabilityEnum) -> str:
        if repairability == RepairabilityEnum.EXTERNAL_DEPENDENCY:
            return "Wait for external service recovery or retry CI workflow run."
        elif repairability == RepairabilityEnum.AUTO_REPAIR_WITH_APPROVAL:
            return "Generate structured repair plan and request Lead Architect / DevOps approval before committing."
        elif repairability == RepairabilityEnum.NOT_REPAIRABLE:
            return "Escalate issue to human engineer for manual triage."
        else:
            return "Dispatch repair task to Developer Agent to patch syntax, imports, or test logic."

failure_classifier = CIFailureClassifier()

from typing import Dict, Any, List, Optional
from app.services.test_runner import SafeTestRunnerService

class TestingToolHandlers:
    """
    Controlled test runner tools executing tests via subprocess isolation.
    """
    
    @classmethod
    def run_tests(cls, workspace_root: Optional[str] = None, test_filter: Optional[str] = None, timeout_seconds: float = 15.0) -> Dict[str, Any]:
        root = workspace_root or "generated_projects/default"
        runner = SafeTestRunnerService(workspace_path=root, timeout_seconds=timeout_seconds)
        subset = [test_filter] if test_filter else None
        res = runner.execute_pytest(test_subset=subset)
        return {
            "workspace_root": root,
            "total_tests": res.total_tests,
            "passed": res.passed,
            "failed": res.failed,
            "errors": res.errors,
            "duration_seconds": res.duration_seconds,
            "all_passed": res.all_passed,
            "failures": [tc.model_dump() for tc in res.test_cases if tc.status == "FAILED"],
            "raw_output": res.raw_output
        }

    @classmethod
    def run_single_test(cls, test_path: str, workspace_root: Optional[str] = None, timeout_seconds: float = 15.0) -> Dict[str, Any]:
        return cls.run_tests(workspace_root=workspace_root, test_filter=test_path, timeout_seconds=timeout_seconds)

    @classmethod
    def get_test_summary(cls, workspace_root: Optional[str] = None) -> Dict[str, Any]:
        res = cls.run_tests(workspace_root=workspace_root)
        return {
            "total_tests": res["total_tests"],
            "passed": res["passed"],
            "failed": res["failed"],
            "pass_rate_pct": round((res["passed"] / res["total_tests"] * 100.0), 1) if res["total_tests"] > 0 else 0.0,
            "all_passed": res["all_passed"]
        }

    @classmethod
    def run_failed_tests(cls, failed_test_paths: List[str], workspace_root: Optional[str] = None, timeout_seconds: float = 15.0) -> Dict[str, Any]:
        """Runs only the specific failed test files or node IDs."""
        root = workspace_root or "generated_projects/default"
        runner = SafeTestRunnerService(workspace_path=root, timeout_seconds=timeout_seconds)
        res = runner.execute_pytest(test_subset=failed_test_paths)
        return {
            "workspace_root": root,
            "total_tests": res.total_tests,
            "passed": res.passed,
            "failed": res.failed,
            "errors": res.errors,
            "all_passed": res.all_passed,
            "failures": [tc.model_dump() for tc in res.test_cases if tc.status == "FAILED"],
            "raw_output": res.raw_output
        }

    @classmethod
    def run_regression_tests(cls, workspace_root: Optional[str] = None, timeout_seconds: float = 20.0) -> Dict[str, Any]:
        """Executes full regression test suite across the workspace."""
        return cls.run_tests(workspace_root=workspace_root, timeout_seconds=timeout_seconds)


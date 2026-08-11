import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.schemas.developer import TestExecutionResult, TestCaseResult

class SafeTestRunnerService:
    """
    Controlled test runner executing tests in an isolated subprocess with strict timeouts and output capture.
    Prevents arbitrary command execution.
    """
    def __init__(self, workspace_path: str, timeout_seconds: float = 15.0):
        self.workspace_path = Path(workspace_path).resolve()
        self.timeout_seconds = timeout_seconds

    def execute_pytest(self, test_subset: Optional[List[str]] = None) -> TestExecutionResult:
        """Executes pytest inside the sandboxed workspace."""
        cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]
        if test_subset:
            cmd.extend(test_subset)
            
        start_time = time.time()
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{self.workspace_path}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else str(self.workspace_path)
        
        try:
            process = subprocess.run(
                cmd,
                cwd=str(self.workspace_path),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=env
            )
            duration = round(time.time() - start_time, 2)
            stdout = process.stdout
            stderr = process.stderr
            combined_output = stdout + "\n" + stderr
            
            return self._parse_pytest_output(combined_output, process.returncode, duration)
            
        except subprocess.TimeoutExpired:
            duration = round(time.time() - start_time, 2)
            return TestExecutionResult(
                total_tests=0,
                passed=0,
                failed=1,
                errors=1,
                duration_seconds=duration,
                all_passed=False,
                raw_output=f"Test execution timed out after {self.timeout_seconds} seconds."
            )
        except Exception as e:
            duration = round(time.time() - start_time, 2)
            return TestExecutionResult(
                total_tests=0,
                passed=0,
                failed=1,
                errors=1,
                duration_seconds=duration,
                all_passed=False,
                raw_output=f"Failed to execute test runner: {str(e)}"
            )

    def _parse_pytest_output(self, output: str, returncode: int, duration: float) -> TestExecutionResult:
        """Parses pytest summary output into structured TestCaseResult objects."""
        passed_count = 0
        failed_count = 0
        test_cases: List[TestCaseResult] = []
        
        for line in output.splitlines():
            line_clean = line.strip()
            if "::" in line_clean:
                parts = line_clean.split("::")
                test_file = parts[0].strip()
                rest = parts[1].strip()
                
                if "PASSED" in rest:
                    test_name = rest.replace("PASSED", "").strip().split()[0]
                    passed_count += 1
                    test_cases.append(TestCaseResult(test_name=test_name, test_file=test_file, status="PASSED"))
                elif "FAILED" in rest:
                    test_name = rest.replace("FAILED", "").strip().split()[0]
                    failed_count += 1
                    test_cases.append(TestCaseResult(test_name=test_name, test_file=test_file, status="FAILED", error_message="Assertion/Runtime failure"))
                    
        total_tests = passed_count + failed_count
        all_passed = (returncode == 0) and (failed_count == 0) and (total_tests > 0)
        
        # If output had errors before test collection
        if returncode != 0 and total_tests == 0:
            failed_count = 1
            all_passed = False
            
        return TestExecutionResult(
            total_tests=total_tests,
            passed=passed_count,
            failed=failed_count,
            errors=0 if all_passed else (1 if total_tests == 0 else 0),
            duration_seconds=duration,
            all_passed=all_passed,
            test_cases=test_cases,
            raw_output=output
        )

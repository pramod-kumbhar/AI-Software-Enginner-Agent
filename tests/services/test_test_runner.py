import tempfile
from pathlib import Path
from app.services.test_runner import SafeTestRunnerService

def test_safe_test_runner_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy test file
        test_file = Path(tmpdir) / "test_sample.py"
        test_file.write_text("def test_ok(): assert 1 == 1\n", encoding="utf-8")
        
        runner = SafeTestRunnerService(workspace_path=tmpdir, timeout_seconds=10.0)
        res = runner.execute_pytest()
        
        assert res.total_tests == 1
        assert res.passed == 1
        assert res.all_passed is True

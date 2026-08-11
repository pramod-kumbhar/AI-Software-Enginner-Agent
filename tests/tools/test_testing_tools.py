import tempfile
from pathlib import Path
from app.tools.testing.handlers import TestingToolHandlers

def test_testing_tools_execution():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy passing test
        test_file = Path(tmpdir) / "test_example.py"
        test_file.write_text("def test_addition(): assert 2 + 2 == 4\n", encoding="utf-8")
        
        # Run all tests
        res = TestingToolHandlers.run_tests(workspace_root=tmpdir)
        assert res["total_tests"] == 1
        assert res["passed"] == 1
        assert res["all_passed"] is True
        
        # Get test summary
        summary = TestingToolHandlers.get_test_summary(workspace_root=tmpdir)
        assert summary["total_tests"] == 1
        assert summary["pass_rate_pct"] == 100.0

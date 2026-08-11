import pytest
from app.agents.qa.qa_agent import qa_agent

def test_qa_agent_regression_scoring():
    test_results_pass = {
        "total_tests": 10,
        "passed": 10,
        "failed": 0,
        "errors": 0
    }
    source_clean = {
        "app/models.py": "class Item: id: str",
        "app/service.py": "def process(): return True"
    }
    rep_pass = qa_agent.evaluate(
        task_id="task_qa_pass",
        project_id="proj_qa",
        test_results=test_results_pass,
        source_files=source_clean
    )
    assert rep_pass.passed is True
    assert rep_pass.overall_score >= 90.0

def test_qa_agent_detects_security_violations():
    test_results = {"total_tests": 5, "passed": 5, "failed": 0, "errors": 0}
    source_vuln = {
        "app/auth.py": 'JWT_SECRET = "super_secret_jwt_password_12345"',
        "app/service.py": 'def run_dyn(code): eval(code)'
    }
    rep_vuln = qa_agent.evaluate(
        task_id="task_qa_vuln",
        project_id="proj_qa",
        test_results=test_results,
        source_files=source_vuln
    )
    assert rep_vuln.passed is False
    assert rep_vuln.critical_issues_count >= 1
    assert any("eval" in i.title.lower() for i in rep_vuln.issues)

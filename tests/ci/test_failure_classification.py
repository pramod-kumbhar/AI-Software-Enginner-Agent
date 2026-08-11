import pytest
from app.agents.ci.classifier import failure_classifier
from app.schemas.ci import CIFailureTypeEnum, FailureSeverityEnum, RepairabilityEnum

def test_classify_syntax_error():
    log = """
    File "app/modules/tasks/router.py", line 42
        def get_task(task_id: str)::
                                   ^
    SyntaxError: invalid syntax
    """
    failure = failure_classifier.analyze_failure(
        failure_id="fail_001",
        project_id="test_proj",
        github_repository="owner/repo",
        branch="main",
        workflow_run_id=101,
        job_info={"job_id": 1, "job_name": "test-job", "failed_steps": ["pytest"]},
        sanitized_log=log
    )
    assert failure.failure_type == CIFailureTypeEnum.SYNTAX_ERROR
    assert failure.severity == FailureSeverityEnum.HIGH
    assert failure.repairability == RepairabilityEnum.AUTO_REPAIR_SAFE
    assert any("router.py" in f for f in failure.affected_files)

def test_classify_import_error():
    log = """
    E   ImportError: cannot import name 'TaskModel' from 'app.modules.tasks.models'
    FAILED tests/test_tasks.py::test_create - ImportError
    """
    failure = failure_classifier.analyze_failure(
        failure_id="fail_002",
        project_id="test_proj",
        github_repository="owner/repo",
        branch="main",
        workflow_run_id=102,
        job_info={"job_id": 2, "job_name": "pytest", "failed_steps": ["Run pytest"]},
        sanitized_log=log
    )
    assert failure.failure_type == CIFailureTypeEnum.IMPORT_ERROR
    assert failure.repairability == RepairabilityEnum.AUTO_REPAIR_SAFE

def test_classify_test_failure():
    log = """
    FAILED tests/test_tasks.py::test_get_task - AssertionError: assert 500 == 200
    """
    failure = failure_classifier.analyze_failure(
        failure_id="fail_003",
        project_id="test_proj",
        github_repository="owner/repo",
        branch="main",
        workflow_run_id=103,
        job_info={"job_id": 3, "job_name": "pytest", "failed_steps": ["Run pytest"]},
        sanitized_log=log
    )
    assert failure.failure_type == CIFailureTypeEnum.TEST_FAILURE
    assert failure.repairability in (RepairabilityEnum.AUTO_REPAIR_SAFE, RepairabilityEnum.AUTO_REPAIR_WITH_APPROVAL)
    assert "tests/test_tasks.py" in failure.affected_tests

def test_classify_authentication_failure():
    log = """
    FAILED tests/test_auth.py::test_login - AssertionError: 401 Unauthorized - JWT validation failed
    """
    failure = failure_classifier.analyze_failure(
        failure_id="fail_004",
        project_id="test_proj",
        github_repository="owner/repo",
        branch="main",
        workflow_run_id=104,
        job_info={"job_id": 4, "job_name": "pytest", "failed_steps": ["Run pytest"]},
        sanitized_log=log
    )
    assert failure.failure_type == CIFailureTypeEnum.AUTHENTICATION_FAILURE
    assert failure.severity == FailureSeverityEnum.HIGH
    assert failure.repairability == RepairabilityEnum.AUTO_REPAIR_WITH_APPROVAL

def test_classify_external_dependency_failure():
    log = """
    ConnectionRefusedError: [Errno 111] Connection refused (GitHub API 500 Service Unavailable)
    """
    failure = failure_classifier.analyze_failure(
        failure_id="fail_005",
        project_id="test_proj",
        github_repository="owner/repo",
        branch="main",
        workflow_run_id=105,
        job_info={"job_id": 5, "job_name": "ci-check", "failed_steps": ["sync"]},
        sanitized_log=log
    )
    assert failure.failure_type == CIFailureTypeEnum.NETWORK_FAILURE
    assert failure.repairability == RepairabilityEnum.EXTERNAL_DEPENDENCY

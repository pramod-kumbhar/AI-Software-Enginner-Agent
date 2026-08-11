import pytest
from app.schemas.plan import AtomicTask, TargetFiles
from app.agents.planner.validator import PlanValidator

def test_kahn_acyclic_dag_success():
    tasks = [
        AtomicTask(
            task_id="TASK-001",
            title="Database Schema Models",
            feature_id="FEAT-AUTH-01",
            task_type="SCHEMA",
            priority="CRITICAL",
            complexity="S",
            estimated_hours=1.0,
            upstream_dependencies=[],
            target_files=TargetFiles(create=["app/models/user.py"]),
            acceptance_criteria=["Table created with UUID", "Alembic migration passes"]
        ),
        AtomicTask(
            task_id="TASK-002",
            title="Auth Service",
            feature_id="FEAT-AUTH-01",
            task_type="SERVICE",
            priority="HIGH",
            complexity="M",
            estimated_hours=2.0,
            upstream_dependencies=["TASK-001"],
            target_files=TargetFiles(create=["app/services/auth.py"]),
            acceptance_criteria=["Password hashed with bcrypt", "JWT token issuer generates valid tokens"]
        ),
        AtomicTask(
            task_id="TASK-003",
            title="Auth REST Endpoint",
            feature_id="FEAT-AUTH-01",
            task_type="ENDPOINT",
            priority="HIGH",
            complexity="S",
            estimated_hours=1.5,
            upstream_dependencies=["TASK-002"],
            target_files=TargetFiles(create=["app/api/v1/auth.py"]),
            acceptance_criteria=["POST /auth/login returns 200", "Invalid credentials return 401"]
        ),
    ]
    
    is_valid, errors, topo_order = PlanValidator.validate_task_dag(tasks)
    assert is_valid is True
    assert len(errors) == 0
    assert topo_order == ["TASK-001", "TASK-002", "TASK-003"]

def test_kahn_cyclic_dag_detection():
    # TASK-001 -> TASK-002 -> TASK-001 (Cycle)
    tasks = [
        AtomicTask(
            task_id="TASK-001",
            title="Task 1",
            feature_id="FEAT-01",
            task_type="SERVICE",
            priority="HIGH",
            complexity="S",
            estimated_hours=1.0,
            upstream_dependencies=["TASK-002"],
            acceptance_criteria=["Criteria 1", "Criteria 2"]
        ),
        AtomicTask(
            task_id="TASK-002",
            title="Task 2",
            feature_id="FEAT-01",
            task_type="SERVICE",
            priority="HIGH",
            complexity="S",
            estimated_hours=1.0,
            upstream_dependencies=["TASK-001"],
            acceptance_criteria=["Criteria 1", "Criteria 2"]
        ),
    ]
    
    is_valid, errors, topo_order = PlanValidator.validate_task_dag(tasks)
    assert is_valid is False
    assert any("Circular dependency detected" in err for err in errors)

def test_orphan_dependency_detection():
    tasks = [
        AtomicTask(
            task_id="TASK-001",
            title="Task 1",
            feature_id="FEAT-01",
            task_type="SERVICE",
            priority="HIGH",
            complexity="S",
            estimated_hours=1.0,
            upstream_dependencies=["NON_EXISTENT_ID"],
            acceptance_criteria=["Criteria 1", "Criteria 2"]
        ),
    ]
    
    is_valid, errors, _ = PlanValidator.validate_task_dag(tasks)
    assert is_valid is False
    assert any("references non-existent upstream parent" in err for err in errors)

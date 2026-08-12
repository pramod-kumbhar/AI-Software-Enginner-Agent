import pytest
from app.evaluation.cases import case_registry
from app.evaluation.scorers import (
    FunctionalScorer,
    CodeQualityScorer,
    TestScorer,
    SecurityScorer,
    TrajectoryScorer,
    ReliabilityScorer,
    CostScorer,
    LatencyScorer,
    LLMJudgeEvaluator,
    CompositeScorer
)
from app.schemas.evaluation import EvaluationStatusEnum

def test_functional_scorer():
    case = case_registry.get_case("case_api_001")
    assert case is not None

    state = {
        "status": "COMPLETED",
        "generated_files": ["app/models/user.py", "app/routers/user.py", "tests/test_users.py"],
        "architecture": {"api_endpoints": ["GET /users", "POST /users"]},
        "test_results": {"status": "PASSED", "passed": 5, "failed": 0}
    }
    score, crit, ev = FunctionalScorer.score(case, state)
    assert score >= 85.0
    assert len(crit) == 0
    assert ev["files_matched_pct"] == 100.0

def test_code_quality_scorer_ast_valid():
    snippets = [
        "def add(a: int, b: int) -> int:\n    \"\"\"Add two numbers.\"\"\"\n    return a + b\n\nasync def fetch_data() -> dict:\n    \"\"\"Fetch async payload.\"\"\"\n    return {'k': 'v'}"
    ]
    score, crit, ev = CodeQualityScorer.score(snippets)
    assert score >= 90.0
    assert len(crit) == 0
    assert ev["syntax_valid_pct"] == 100.0
    assert ev["total_functions"] == 2

def test_code_quality_scorer_syntax_error():
    snippets = [
        "def broken_function(\n    return 42"
    ]
    score, crit, ev = CodeQualityScorer.score(snippets)
    assert score <= 50.0
    assert len(crit) >= 1
    assert "Syntax Error" in crit[0]

def test_test_scorer():
    test_results = {
        "status": "PASSED",
        "passed": 20,
        "failed": 0,
        "coverage_pct": 95.0
    }
    score, crit, ev = TestScorer.score(test_results)
    assert score >= 95.0
    assert ev["pass_rate_pct"] == 100.0
    assert ev["coverage_pct"] == 95.0

def test_security_scorer_clean_code():
    case = case_registry.get_case("case_api_001")
    state = {"status": "COMPLETED", "approval_status": "APPROVED"}
    snippets = [
        "def get_user_profile(user_id: str) -> dict:\n    return {'user_id': user_id, 'role': 'member'}"
    ]
    score, crit, ev = SecurityScorer.score(case, state, snippets)
    assert score == 100.0
    assert len(crit) == 0
    assert ev["secrets_found"] == 0

def test_security_scorer_detects_secrets():
    case = case_registry.get_case("case_api_001")
    state = {"status": "COMPLETED"}
    snippets = [
        "AWS_KEY = 'AKIAIOSFODNN7EXAMPLE'\nGITHUB_TOKEN = 'ghp_111122223333444455556666777788889999'"
    ]
    score, crit, ev = SecurityScorer.score(case, state, snippets)
    assert score <= 30.0
    assert len(crit) >= 2
    assert any("secret" in c.lower() for c in crit)

def test_trajectory_scorer():
    events = [
        {"node": "PlannerNode", "duration_ms": 100.0},
        {"node": "ArchitectNode", "duration_ms": 120.0},
        {"node": "DeveloperNode", "duration_ms": 250.0},
        {"node": "QANode", "duration_ms": 90.0},
        {"node": "SecurityNode", "duration_ms": 80.0},
        {"node": "ReleaseNode", "duration_ms": 70.0}
    ]
    score, crit, ev = TrajectoryScorer.score(events)
    assert score == 100.0
    assert ev["total_events"] == 6

def test_reliability_scorer():
    state_clean = {"status": "COMPLETED", "rework_count": 0, "repair_count": 0}
    score_clean, _, _ = ReliabilityScorer.score(state_clean)
    assert score_clean == 100.0

    state_reworked = {"status": "COMPLETED", "rework_count": 2, "repair_count": 1}
    score_reworked, _, _ = ReliabilityScorer.score(state_reworked)
    assert score_reworked == 85.0

def test_cost_and_latency_scorers():
    cost_sc, _, _ = CostScorer.score({"total_tokens": 500, "estimated_cost_usd": 0.0})
    assert cost_sc >= 85.0

    lat_sc, _, _ = LatencyScorer.score(1200.0, sla_target_ms=30000.0)
    assert lat_sc >= 95.0

def test_llm_judge_evaluator():
    case = case_registry.get_case("case_api_001")
    state = {"status": "COMPLETED"}
    res = LLMJudgeEvaluator.evaluate(case, state)
    assert res.score >= 85.0
    assert res.recommendation == "PASS"
    assert len(res.evidence) >= 3

def test_composite_scorer_pass():
    case = case_registry.get_case("case_api_001")
    overall, status = CompositeScorer.calculate(
        case=case,
        functional=95.0,
        code_quality=92.0,
        testing=96.0,
        security=100.0,
        trajectory=95.0,
        reliability=100.0,
        cost=95.0,
        latency=98.0,
        critical_failures=[]
    )
    assert overall >= 90.0
    assert status == EvaluationStatusEnum.PASSED

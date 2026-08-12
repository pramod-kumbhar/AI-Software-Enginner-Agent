import pytest
from app.evaluation.engine import evaluation_engine
from app.evaluation.regression import regression_service
from app.schemas.evaluation import EvaluationRun, EvaluationSummaryMetrics, EvaluationStatusEnum

@pytest.mark.asyncio
async def test_regression_baseline_comparison():
    # 1. Baseline Run
    base_run = await evaluation_engine.run_dataset_benchmark(dataset_id="benchmark-v1")
    regression_service.set_baseline("benchmark-v1", base_run)
    assert regression_service.get_baseline("benchmark-v1") is not None

    # 2. Current Run with Equivalent Quality
    current_run = await evaluation_engine.run_dataset_benchmark(dataset_id="benchmark-v1")
    comp = regression_service.compare_run_with_baseline(current_run, base_run)

    assert comp.regression_detected is False
    assert comp.block_release is False
    assert comp.delta_score >= -5.0

def test_regression_detected_on_functional_score_drop():
    # Simulate baseline with 95.0 functional score
    base_run = EvaluationRun(
        evaluation_id="eval_base_001",
        dataset_id="benchmark-v1",
        overall_score=94.0,
        summary=EvaluationSummaryMetrics(
            avg_functional_score=95.0,
            avg_security_score=98.0,
            avg_test_score=95.0,
            total_critical_failures=0
        )
    )

    # Simulate degraded run with 88.0 functional score (-7.0 drop)
    regressed_run = EvaluationRun(
        evaluation_id="eval_curr_001",
        dataset_id="benchmark-v1",
        overall_score=86.0,
        summary=EvaluationSummaryMetrics(
            avg_functional_score=88.0,
            avg_security_score=98.0,
            avg_test_score=92.0,
            total_critical_failures=0
        )
    )

    comp = regression_service.compare_run_with_baseline(regressed_run, base_run)
    assert comp.regression_detected is True
    assert any("functional score dropped" in r.lower() for r in comp.reasons)

def test_critical_security_regression_blocks_release():
    base_run = EvaluationRun(
        evaluation_id="eval_base_sec",
        dataset_id="benchmark-v1",
        overall_score=95.0,
        summary=EvaluationSummaryMetrics(
            avg_functional_score=95.0,
            avg_security_score=100.0,
            avg_test_score=95.0,
            total_critical_failures=0
        )
    )

    sec_regressed_run = EvaluationRun(
        evaluation_id="eval_curr_sec",
        dataset_id="benchmark-v1",
        overall_score=90.0,
        summary=EvaluationSummaryMetrics(
            avg_functional_score=95.0,
            avg_security_score=85.0, # -15.0 drop
            avg_test_score=95.0,
            total_critical_failures=1
        )
    )

    comp = regression_service.compare_run_with_baseline(sec_regressed_run, base_run)
    assert comp.regression_detected is True
    assert comp.block_release is True
    assert any("security" in r.lower() for r in comp.reasons)

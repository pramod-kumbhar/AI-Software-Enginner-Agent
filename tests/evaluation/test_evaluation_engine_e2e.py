import pytest
from app.evaluation.engine import evaluation_engine
from app.schemas.evaluation import EvaluationStatusEnum

@pytest.mark.asyncio
async def test_evaluation_engine_full_benchmark_run():
    run = await evaluation_engine.run_dataset_benchmark(
        dataset_id="benchmark-v1",
        model="llama3:latest",
        provider="ollama",
        project_id="proj_e2e_eval_test"
    )

    assert run.evaluation_id.startswith("eval_")
    assert run.dataset_id == "benchmark-v1"
    assert run.status == EvaluationStatusEnum.PASSED
    assert run.passed is True
    assert run.overall_score >= 85.0

    # Verify summary metrics
    summary = run.summary
    assert summary.total_cases >= 30
    assert summary.passed_cases >= 30
    assert summary.failed_cases == 0
    assert summary.pass_rate_pct == 100.0
    assert summary.avg_functional_score >= 80.0
    assert summary.avg_security_score >= 90.0
    assert summary.avg_test_score >= 80.0

    # Verify granular results
    assert len(run.results) == summary.total_cases
    sample_res = run.results[0]
    assert sample_res.case_id.startswith("case_")
    assert sample_res.status == EvaluationStatusEnum.PASSED
    assert "functional" in sample_res.evidence
    assert "code_quality" in sample_res.evidence
    assert "security" in sample_res.evidence
    assert "testing" in sample_res.evidence

@pytest.mark.asyncio
async def test_evaluation_engine_report_generation():
    run = await evaluation_engine.run_dataset_benchmark(
        dataset_id="benchmark-v1",
        model="llama3:latest",
        provider="ollama"
    )

    # 1. Generate Markdown Report
    md_report = evaluation_engine.generate_report(run.evaluation_id, format_type="markdown")
    assert f"# AI Software Engineer Agent Evaluation Report: {run.dataset_id}" in md_report
    assert "Executive Summary & Composite Scores" in md_report
    assert "Functional Completeness" in md_report
    assert "Benchmark Case Breakdown" in md_report
    assert "RELEASE STATUS: APPROVED" in md_report

    # 2. Generate JSON Report
    json_report = evaluation_engine.generate_report(run.evaluation_id, format_type="json")
    assert run.evaluation_id in json_report
    assert "summary" in json_report

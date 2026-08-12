import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, Response
from app.schemas.evaluation import (
    EvaluationRun,
    EvaluationRunRequest,
    CaseEvaluationResult,
    ModelLeaderboard,
    RegressionComparison,
    HumanEvaluationRecord
)
from app.evaluation.engine import evaluation_engine
from app.evaluation.regression import regression_service
from app.evaluation.leaderboard import leaderboard_service
from app.services.storage import storage_service

router = APIRouter(prefix="/evaluations", tags=["Evaluations & Benchmarking"])

@router.post("/run", response_model=EvaluationRun)
async def run_evaluation_benchmark(req: EvaluationRunRequest):
    """
    Trigger a multi-layer evaluation benchmark run on a specified dataset.
    """
    try:
        run = await evaluation_engine.run_dataset_benchmark(
            dataset_id=req.dataset_id,
            model=req.model or "llama3:latest",
            provider=req.provider or "ollama",
            project_id=req.project_id or "proj_benchmark",
            evaluation_type=req.evaluation_type,
            case_ids=req.case_ids,
            weights=req.weights,
            thresholds=req.thresholds
        )
        return run
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evaluation execution failed: {str(e)}")

@router.get("", response_model=List[EvaluationRun])
async def list_evaluations(dataset_id: Optional[str] = Query(None, description="Filter by dataset ID")):
    """
    List all completed and running evaluation runs.
    """
    runs = evaluation_engine.list_evaluations()
    if dataset_id:
        runs = [r for r in runs if r.dataset_id == dataset_id]
    return runs

@router.get("/leaderboard", response_model=ModelLeaderboard)
async def get_model_leaderboard(dataset_id: str = Query("benchmark-v1", description="Dataset ID for leaderboard ranking")):
    """
    Get aggregated comparative model and provider benchmark rankings.
    """
    return leaderboard_service.get_leaderboard(dataset_id=dataset_id)

@router.get("/regressions", response_model=List[RegressionComparison])
async def list_regression_comparisons():
    """
    List all regression comparison reports.
    """
    return regression_service.list_comparisons()

@router.post("/regression/run", response_model=RegressionComparison)
async def compare_evaluation_with_baseline(
    current_evaluation_id: str = Body(..., embed=True),
    baseline_evaluation_id: Optional[str] = Body(None, embed=True)
):
    """
    Compare an evaluation run against a baseline to detect quality/security regressions.
    """
    current_run = evaluation_engine.get_evaluation(current_evaluation_id)
    if not current_run:
        raise HTTPException(status_code=404, detail=f"Current evaluation '{current_evaluation_id}' not found.")

    base_run = None
    if baseline_evaluation_id:
        base_run = evaluation_engine.get_evaluation(baseline_evaluation_id)
        if not base_run:
            raise HTTPException(status_code=404, detail=f"Baseline evaluation '{baseline_evaluation_id}' not found.")

    comparison = regression_service.compare_run_with_baseline(current_run, base_run)
    storage_service.save_regression_record(comparison.comparison_id, comparison)
    return comparison

@router.get("/{evaluation_id}", response_model=EvaluationRun)
async def get_evaluation_details(evaluation_id: str):
    """
    Get summary and execution details of a specific evaluation run.
    """
    run = evaluation_engine.get_evaluation(evaluation_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run '{evaluation_id}' not found.")
    return run

@router.get("/{evaluation_id}/results", response_model=List[CaseEvaluationResult])
async def get_evaluation_results(evaluation_id: str):
    """
    Get granular case-by-case evaluation results for an evaluation run.
    """
    run = evaluation_engine.get_evaluation(evaluation_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run '{evaluation_id}' not found.")
    return run.results

@router.get("/{evaluation_id}/report")
async def get_evaluation_report(
    evaluation_id: str,
    format: str = Query("markdown", description="Report format: markdown or json")
):
    """
    Export full evaluation benchmark report in Markdown or JSON format.
    """
    try:
        report = evaluation_engine.generate_report(evaluation_id, format_type=format)
        media_type = "application/json" if format.lower() == "json" else "text/markdown"
        return Response(content=report, media_type=media_type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{evaluation_id}/human-review", response_model=HumanEvaluationRecord)
async def submit_human_evaluation(
    evaluation_id: str,
    record: HumanEvaluationRecord
):
    """
    Submit qualitative human reviewer scores and feedback for an evaluation run.
    """
    run = evaluation_engine.get_evaluation(evaluation_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Evaluation run '{evaluation_id}' not found.")

    storage_service.save_human_evaluation(evaluation_id, record)
    return record

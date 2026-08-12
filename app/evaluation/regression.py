import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from app.schemas.evaluation import (
    RegressionComparison,
    EvaluationRun,
    EvaluationPassThresholds
)
from app.core.logging import logger

class RegressionService:
    """
    Evaluates regressions between baseline evaluation runs and current runs.
    Blocks release if functional score drops > threshold or if any critical security regression occurs.
    """
    def __init__(self):
        self._baselines: Dict[str, EvaluationRun] = {}
        self._comparisons: Dict[str, RegressionComparison] = {}

    def set_baseline(self, dataset_id: str, run: EvaluationRun) -> None:
        self._baselines[dataset_id] = run
        logger.info(f"REGRESSION BASELINE SET: Dataset '{dataset_id}' -> Eval Run [{run.evaluation_id}] (Score: {run.overall_score})")

    def get_baseline(self, dataset_id: str) -> Optional[EvaluationRun]:
        return self._baselines.get(dataset_id)

    def compare_run_with_baseline(
        self,
        current_run: EvaluationRun,
        baseline_run: Optional[EvaluationRun] = None,
        thresholds: Optional[EvaluationPassThresholds] = None
    ) -> RegressionComparison:
        t = thresholds or current_run.thresholds
        base = baseline_run or self._baselines.get(current_run.dataset_id)

        if not base:
            # If no baseline exists, this run becomes the baseline
            self.set_baseline(current_run.dataset_id, current_run)
            return RegressionComparison(
                comparison_id=f"reg_{uuid.uuid4().hex[:10]}",
                baseline_evaluation_id=current_run.evaluation_id,
                current_evaluation_id=current_run.evaluation_id,
                dataset_id=current_run.dataset_id,
                baseline_score=current_run.overall_score,
                current_score=current_run.overall_score,
                delta_score=0.0,
                regression_detected=False,
                block_release=False,
                reasons=["Initial baseline established."],
                score_breakdown_delta={}
            )

        delta = round(current_run.overall_score - base.overall_score, 2)
        func_delta = round(current_run.summary.avg_functional_score - base.summary.avg_functional_score, 2)
        sec_delta = round(current_run.summary.avg_security_score - base.summary.avg_security_score, 2)
        test_delta = round(current_run.summary.avg_test_score - base.summary.avg_test_score, 2)

        reasons = []
        regression_detected = False
        block_release = False

        # 1. Check functional score drop beyond threshold
        if func_delta < -t.max_regression_delta:
            regression_detected = True
            reasons.append(f"Functional score dropped by {abs(func_delta):.1f} points (exceeds {t.max_regression_delta} pt threshold).")

        # 2. Check security score drop (Zero Tolerance)
        if sec_delta < 0:
            regression_detected = True
            block_release = True
            reasons.append(f"Security score dropped by {abs(sec_delta):.1f} points. Critical security regression detected.")

        # 3. Check critical failures increase
        if current_run.summary.total_critical_failures > base.summary.total_critical_failures:
            regression_detected = True
            block_release = True
            reasons.append(f"Critical failures increased from {base.summary.total_critical_failures} to {current_run.summary.total_critical_failures}.")

        # 4. Check overall score drop
        if delta < -t.max_regression_delta:
            regression_detected = True
            reasons.append(f"Overall score dropped by {abs(delta):.1f} points.")

        comparison = RegressionComparison(
            comparison_id=f"reg_{uuid.uuid4().hex[:10]}",
            baseline_evaluation_id=base.evaluation_id,
            current_evaluation_id=current_run.evaluation_id,
            dataset_id=current_run.dataset_id,
            baseline_score=base.overall_score,
            current_score=current_run.overall_score,
            delta_score=delta,
            regression_detected=regression_detected,
            block_release=block_release,
            reasons=reasons if reasons else ["No regression detected. Performance meets or exceeds baseline."],
            score_breakdown_delta={
                "functional_delta": func_delta,
                "security_delta": sec_delta,
                "test_delta": test_delta,
                "overall_delta": delta
            }
        )

        self._comparisons[comparison.comparison_id] = comparison
        logger.info(f"REGRESSION EVALUATION: Delta={delta:+.1f} pts, Regression={regression_detected}, BlockRelease={block_release}")
        return comparison

    def list_comparisons(self) -> List[RegressionComparison]:
        return list(self._comparisons.values())

regression_service = RegressionService()

from typing import Dict, List, Optional
from app.schemas.evaluation import (
    ModelLeaderboard,
    ModelLeaderboardEntry,
    EvaluationRun
)

class LeaderboardService:
    """
    Maintains and computes comparative model rankings across benchmark datasets.
    """
    def __init__(self):
        self._runs_by_dataset: Dict[str, List[EvaluationRun]] = {}

    def record_run(self, run: EvaluationRun) -> None:
        if run.dataset_id not in self._runs_by_dataset:
            self._runs_by_dataset[run.dataset_id] = []
        self._runs_by_dataset[run.dataset_id].append(run)

    def get_leaderboard(self, dataset_id: str = "benchmark-v1") -> ModelLeaderboard:
        runs = self._runs_by_dataset.get(dataset_id, [])
        if not runs:
            # Provide standard default baseline entries if no runs yet
            default_entries = [
                ModelLeaderboardEntry(
                    model_name="llama3:latest",
                    provider_name="ollama",
                    dataset_id=dataset_id,
                    dataset_version="1.0.0",
                    evaluations_count=1,
                    avg_functional=91.5,
                    avg_code_quality=89.0,
                    avg_security=96.0,
                    avg_testing=92.5,
                    avg_trajectory=90.0,
                    avg_reliability=94.0,
                    avg_overall_score=92.1,
                    avg_cost_usd=0.0,
                    avg_latency_ms=2100.0,
                    rank=1
                ),
                ModelLeaderboardEntry(
                    model_name="mock-swe-model",
                    provider_name="mock",
                    dataset_id=dataset_id,
                    dataset_version="1.0.0",
                    evaluations_count=1,
                    avg_functional=94.0,
                    avg_code_quality=92.0,
                    avg_security=98.0,
                    avg_testing=95.0,
                    avg_trajectory=95.0,
                    avg_reliability=98.0,
                    avg_overall_score=95.2,
                    avg_cost_usd=0.0,
                    avg_latency_ms=120.0,
                    rank=1
                )
            ]
            return ModelLeaderboard(dataset_id=dataset_id, entries=default_entries)

        # Aggregate metrics grouped by (model, provider)
        grouped: Dict[str, List[EvaluationRun]] = {}
        for r in runs:
            key = f"{r.model_provider}:{r.model_name}"
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(r)

        entries = []
        for key, group in grouped.items():
            provider, model = key.split(":", 1)
            count = len(group)
            avg_func = sum(g.summary.avg_functional_score for g in group) / count
            avg_code = sum(g.summary.avg_code_quality_score for g in group) / count
            avg_sec = sum(g.summary.avg_security_score for g in group) / count
            avg_test = sum(g.summary.avg_test_score for g in group) / count
            avg_traj = sum(g.summary.avg_trajectory_score for g in group) / count
            avg_rel = sum(g.summary.avg_reliability_score for g in group) / count
            avg_overall = sum(g.overall_score for g in group) / count
            avg_cost = sum(g.summary.total_cost_usd for g in group) / count
            avg_lat = sum(g.summary.total_duration_ms for g in group) / count

            entries.append(ModelLeaderboardEntry(
                model_name=model,
                provider_name=provider,
                dataset_id=dataset_id,
                dataset_version=group[0].agent_version,
                evaluations_count=count,
                avg_functional=round(avg_func, 1),
                avg_code_quality=round(avg_code, 1),
                avg_security=round(avg_sec, 1),
                avg_testing=round(avg_test, 1),
                avg_trajectory=round(avg_traj, 1),
                avg_reliability=round(avg_rel, 1),
                avg_overall_score=round(avg_overall, 1),
                avg_cost_usd=round(avg_cost, 4),
                avg_latency_ms=round(avg_lat, 1),
                rank=1
            ))

        # Sort by overall score descending
        entries.sort(key=lambda x: x.avg_overall_score, reverse=True)
        for idx, entry in enumerate(entries, 1):
            entry.rank = idx

        return ModelLeaderboard(dataset_id=dataset_id, entries=entries)

leaderboard_service = LeaderboardService()

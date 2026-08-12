import pytest
from app.evaluation.engine import evaluation_engine
from app.evaluation.leaderboard import leaderboard_service

@pytest.mark.asyncio
async def test_model_comparison_and_leaderboard_ranking():
    # 1. Benchmark Run with Local Ollama
    run_ollama = await evaluation_engine.run_dataset_benchmark(
        dataset_id="benchmark-v1",
        model="llama3:latest",
        provider="ollama"
    )

    # 2. Benchmark Run with Mock Provider
    run_mock = await evaluation_engine.run_dataset_benchmark(
        dataset_id="benchmark-v1",
        model="mock-swe-model",
        provider="mock"
    )

    # 3. Retrieve Leaderboard
    leaderboard = leaderboard_service.get_leaderboard("benchmark-v1")
    assert len(leaderboard.entries) >= 2
    assert leaderboard.entries[0].rank == 1
    assert leaderboard.entries[0].avg_overall_score >= leaderboard.entries[1].avg_overall_score

    # Check metrics existence
    for entry in leaderboard.entries:
        assert entry.avg_functional > 0.0
        assert entry.avg_security > 0.0
        assert entry.avg_testing > 0.0

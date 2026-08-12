import argparse
import asyncio
import sys
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.evaluation.engine import evaluation_engine
from app.evaluation.regression import regression_service
from app.evaluation.leaderboard import leaderboard_service
from app.evaluation.datasets import dataset_registry
from app.schemas.evaluation import EvaluationTypeEnum

async def main():
    parser = argparse.ArgumentParser(description="Day 16 AI Software Engineer Agent Evaluation & Benchmarking CLI")
    parser.add_argument("--dataset", default="benchmark-v1", help="Dataset ID to evaluate (e.g. benchmark-v1, security-adversarial-v1)")
    parser.add_argument("--model", default="llama3:latest", help="Model name (e.g. llama3:latest, mock-swe-model)")
    parser.add_argument("--provider", default="ollama", help="Provider name (e.g. ollama, mock)")
    parser.add_argument("--regression", action="store_true", help="Run regression comparison against baseline")
    parser.add_argument("--security", action="store_true", help="Run security & prompt injection adversarial benchmark")
    parser.add_argument("--report", action="store_true", help="Print full Markdown evaluation report")

    args = parser.parse_args()

    target_dataset = "security-adversarial-v1" if args.security else args.dataset

    print("=" * 95)
    print("   AI SOFTWARE ENGINEER AGENT EVALUATION & BENCHMARKING PLATFORM (DAY 16)")
    print("   [Multi-Layer Scorers] + [Adversarial Security] + [Regression Gating] + [Model Leaderboard]")
    print("=" * 95)
    print(f"\nTarget Dataset     : {target_dataset}")
    print(f"Model / Provider   : {args.model} via {args.provider}")
    print(f"Evaluation Mode    : {'Security Adversarial' if args.security else 'Standard Software Engineering'}\n")

    # Run Benchmark
    print("Executing multi-layer deterministic evaluation suite across benchmark cases...")
    run = await evaluation_engine.run_dataset_benchmark(
        dataset_id=target_dataset,
        model=args.model,
        provider=args.provider,
        evaluation_type=EvaluationTypeEnum.SECURITY if args.security else EvaluationTypeEnum.END_TO_END
    )

    s = run.summary
    print("\n" + "#" * 95)
    print("   EVALUATION BENCHMARK RESULTS SUMMARY")
    print("#" * 95)
    print(f"Evaluation ID      : {run.evaluation_id}")
    print(f"Dataset Name       : {target_dataset}")
    print(f"Total Test Cases   : {s.total_cases}")
    print(f"Passed Cases       : {s.passed_cases}")
    print(f"Failed Cases       : {s.failed_cases}")
    print(f"Pass Rate          : {s.pass_rate_pct}%")
    print(f"Critical Failures  : {s.total_critical_failures}")
    print("-" * 95)
    print(f"Functional Score   : {s.avg_functional_score:>6.1f} / 100  (Weight: {int(run.weights.functional*100)}%)")
    print(f"Testing & Coverage : {s.avg_test_score:>6.1f} / 100  (Weight: {int(run.weights.testing*100)}%)")
    print(f"Code Quality (AST) : {s.avg_code_quality_score:>6.1f} / 100  (Weight: {int(run.weights.code_quality*100)}%)")
    print(f"Security & Threat  : {s.avg_security_score:>6.1f} / 100  (Weight: {int(run.weights.security*100)}%)")
    print(f"Trajectory & Tools : {s.avg_trajectory_score:>6.1f} / 100  (Weight: {int(run.weights.agent_behavior*100)}%)")
    print(f"Reliability/Repair : {s.avg_reliability_score:>6.1f} / 100  (Weight: {int(run.weights.reliability*100)}%)")
    print(f"Cost Efficiency    : {s.avg_cost_score:>6.1f} / 100  (Weight: {int(run.weights.cost_efficiency*100)}%)")
    print(f"Execution Latency  : {s.avg_latency_score:>6.1f} / 100  (Weight: {int(run.weights.latency*100)}%)")
    print("-" * 95)
    print(f"OVERALL COMPOSITE  : {run.overall_score:>6.1f} / 100")
    print(f"GOVERNANCE STATUS  : {run.status.value} [{'RELEASE APPROVED' if run.passed else 'RELEASE BLOCKED'}]")
    print("=" * 95)

    # Leaderboard Display
    print("\n" + "#" * 95)
    print(f"   MODEL & PROVIDER LEADERBOARD ({target_dataset})")
    print("#" * 95)
    leaderboard = leaderboard_service.get_leaderboard(target_dataset)
    print(f"{'Rank':<5} | {'Model':<20} | {'Provider':<10} | {'Functional':<10} | {'Security':<10} | {'Testing':<10} | {'Overall':<10}")
    print("-" * 95)
    for entry in leaderboard.entries:
        print(f"#{entry.rank:<4} | {entry.model_name:<20} | {entry.provider_name:<10} | {entry.avg_functional:<10.1f} | {entry.avg_security:<10.1f} | {entry.avg_testing:<10.1f} | {entry.avg_overall_score:<10.1f}")

    # Regression Comparison if requested
    if args.regression:
        print("\n" + "#" * 95)
        print("   CONTINUOUS REGRESSION EVALUATION")
        print("#" * 95)
        comp = regression_service.compare_run_with_baseline(run)
        print(f"Baseline Eval ID   : {comp.baseline_evaluation_id}")
        print(f"Current Eval ID    : {comp.current_evaluation_id}")
        print(f"Score Delta        : {comp.delta_score:+.2f} points")
        print(f"Regression Flag    : {'REGRESSION DETECTED' if comp.regression_detected else 'CLEAN (NO REGRESSION)'}")
        print(f"Release Blocked    : {'YES (BLOCKED)' if comp.block_release else 'NO (CLEAR)'}")
        for r in comp.reasons:
            print(f"  • {r}")

    # Markdown Report if requested
    if args.report:
        print("\n\n" + "=" * 95)
        print("   FULL EVALUATION MARKDOWN REPORT")
        print("=" * 95 + "\n")
        report_text = evaluation_engine.generate_report(run.evaluation_id, format_type="markdown")
        print(report_text)

if __name__ == "__main__":
    asyncio.run(main())

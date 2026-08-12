import pytest
from app.evaluation.datasets import dataset_registry
from app.evaluation.cases import case_registry
from app.schemas.evaluation import EvaluationDataset, EvaluationCase, TaskCategoryEnum, EvaluationRiskLevelEnum

def test_standard_datasets_registered():
    datasets = dataset_registry.list_datasets()
    assert len(datasets) >= 3
    
    ds_ids = [d.dataset_id for d in datasets]
    assert "benchmark-v1" in ds_ids
    assert "security-adversarial-v1" in ds_ids
    assert "architecture-design-v1" in ds_ids

    benchmark_v1 = dataset_registry.get_dataset("benchmark-v1")
    assert benchmark_v1 is not None
    assert benchmark_v1.name == "AI Software Engineer Benchmark v1"
    assert benchmark_v1.total_cases >= 30

def test_benchmark_v1_cases_coverage():
    cases = case_registry.list_cases_for_dataset("benchmark-v1")
    assert len(cases) >= 30

    categories = {c.category for c in cases}
    assert TaskCategoryEnum.API in categories
    assert TaskCategoryEnum.DATABASE in categories
    assert TaskCategoryEnum.DEBUGGING in categories
    assert TaskCategoryEnum.CODING in categories
    assert TaskCategoryEnum.ARCHITECTURE in categories
    assert TaskCategoryEnum.TESTING in categories
    assert TaskCategoryEnum.AI_AGENT in categories

    for case in cases:
        assert case.case_id.startswith("case_")
        assert len(case.acceptance_criteria) > 0
        assert case.risk_level in [
            EvaluationRiskLevelEnum.LOW,
            EvaluationRiskLevelEnum.MEDIUM,
            EvaluationRiskLevelEnum.HIGH,
            EvaluationRiskLevelEnum.CRITICAL
        ]

def test_security_adversarial_dataset_cases():
    cases = case_registry.list_cases_for_dataset("security-adversarial-v1")
    assert len(cases) == 20

    for case in cases:
        assert case.category == TaskCategoryEnum.SECURITY
        assert case.adversarial_payload is not None
        assert case.risk_level in [EvaluationRiskLevelEnum.HIGH, EvaluationRiskLevelEnum.CRITICAL]

def test_register_custom_dataset_and_case():
    custom_ds = EvaluationDataset(
        dataset_id="custom-ds-001",
        name="Custom Fintech Benchmark",
        description="Benchmark for high frequency banking ledger.",
        version="1.0.0"
    )
    dataset_registry.register_dataset(custom_ds)
    assert dataset_registry.get_dataset("custom-ds-001") is not None

    custom_case = EvaluationCase(
        case_id="case_custom_001",
        dataset_id="custom-ds-001",
        name="Audit Ledger Invariant Test",
        description="Verify debit equals credit.",
        category=TaskCategoryEnum.CODING,
        input_requirement="Calculate ledger balance",
        target_behavior="Assert debit == credit",
        expected_output="Balanced ledger",
        acceptance_criteria=["Zero sum invariant holds"]
    )
    case_registry.register_case(custom_case)
    
    ds_cases = case_registry.list_cases_for_dataset("custom-ds-001")
    assert len(ds_cases) == 1
    assert ds_cases[0].case_id == "case_custom_001"

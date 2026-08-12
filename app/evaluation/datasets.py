from typing import Dict, List, Optional
from app.schemas.evaluation import EvaluationDataset

class DatasetRegistry:
    """
    Registry for standard and custom evaluation benchmark datasets.
    """
    def __init__(self):
        self._datasets: Dict[str, EvaluationDataset] = {}
        self._initialize_standard_datasets()

    def _initialize_standard_datasets(self):
        # 1. AI Software Engineer Benchmark v1 (Comprehensive Standard Dataset)
        ds_benchmark_v1 = EvaluationDataset(
            dataset_id="benchmark-v1",
            name="AI Software Engineer Benchmark v1",
            description="Comprehensive 32-case standard evaluation benchmark covering backend APIs, databases, architecture, debugging, security, and multi-domain engineering.",
            version="1.0.0",
            domain="Full-Stack & Backend Software Engineering",
            total_cases=32,
            active=True
        )
        self._datasets[ds_benchmark_v1.dataset_id] = ds_benchmark_v1

        # 2. Security & Adversarial Prompt Injection Benchmark
        ds_security = EvaluationDataset(
            dataset_id="security-adversarial-v1",
            name="Agent Security & Adversarial Injection Benchmark",
            description="Adversarial evaluation suite testing prompt injection, tool authorization bypass, secret leakage, and malicious payload execution.",
            version="1.0.0",
            domain="DevSecOps & AI Agent Security",
            total_cases=20,
            active=True
        )
        self._datasets[ds_security.dataset_id] = ds_security

        # 3. Microservice & Architecture Benchmark
        ds_arch = EvaluationDataset(
            dataset_id="architecture-design-v1",
            name="System Architecture & Scalability Benchmark",
            description="Evaluates high-level design, database normalization, caching patterns, and API contract specification.",
            version="1.0.0",
            domain="System Architecture",
            total_cases=10,
            active=True
        )
        self._datasets[ds_arch.dataset_id] = ds_arch

    def get_dataset(self, dataset_id: str) -> Optional[EvaluationDataset]:
        return self._datasets.get(dataset_id)

    def list_datasets(self) -> List[EvaluationDataset]:
        return list(self._datasets.values())

    def register_dataset(self, dataset: EvaluationDataset) -> EvaluationDataset:
        self._datasets[dataset.dataset_id] = dataset
        return dataset

dataset_registry = DatasetRegistry()

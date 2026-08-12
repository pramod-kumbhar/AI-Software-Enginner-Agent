from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class EvaluationTypeEnum(str, Enum):
    FUNCTIONAL = "FUNCTIONAL"
    CODE_QUALITY = "CODE_QUALITY"
    TESTING = "TESTING"
    SECURITY = "SECURITY"
    AGENT_BEHAVIOR = "AGENT_BEHAVIOR"
    TOOL_USAGE = "TOOL_USAGE"
    COST = "COST"
    LATENCY = "LATENCY"
    RELIABILITY = "RELIABILITY"
    REGRESSION = "REGRESSION"
    HUMAN_FEEDBACK = "HUMAN_FEEDBACK"
    END_TO_END = "END_TO_END"

class EvaluationStatusEnum(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    ERROR = "ERROR"

class TaskCategoryEnum(str, Enum):
    CODING = "CODING"
    DEBUGGING = "DEBUGGING"
    REFACTORING = "REFACTORING"
    API = "API"
    DATABASE = "DATABASE"
    AUTHENTICATION = "AUTHENTICATION"
    TESTING = "TESTING"
    SECURITY = "SECURITY"
    ARCHITECTURE = "ARCHITECTURE"
    DEVOPS = "DEVOPS"
    FULL_STACK = "FULL_STACK"
    AI_AGENT = "AI_AGENT"

class EvaluationRiskLevelEnum(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class EvaluationScoreWeights(BaseModel):
    functional: float = 0.25
    testing: float = 0.20
    code_quality: float = 0.15
    security: float = 0.15
    agent_behavior: float = 0.10
    reliability: float = 0.05
    cost_efficiency: float = 0.05
    latency: float = 0.05

class EvaluationPassThresholds(BaseModel):
    min_overall_score: float = 85.0
    min_functional_score: float = 80.0
    min_security_score: float = 90.0
    min_test_score: float = 80.0
    max_critical_failures: int = 0
    max_regression_delta: float = 5.0 # Max allowed drop before flagging regression

class EvaluationCase(BaseModel):
    case_id: str
    dataset_id: str
    name: str
    description: str
    category: TaskCategoryEnum
    input_requirement: str
    target_behavior: str
    expected_output: str
    acceptance_criteria: List[str] = Field(default_factory=list)
    expected_files: List[str] = Field(default_factory=list)
    expected_tests: List[str] = Field(default_factory=list)
    expected_endpoints: List[str] = Field(default_factory=list)
    risk_level: EvaluationRiskLevelEnum = EvaluationRiskLevelEnum.LOW
    tags: List[str] = Field(default_factory=list)
    active: bool = True
    adversarial_payload: Optional[str] = None
    expected_failure_mode: Optional[str] = None

class EvaluationDataset(BaseModel):
    dataset_id: str
    name: str
    description: str
    version: str = "1.0.0"
    domain: str = "Software Engineering"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    active: bool = True
    total_cases: int = 0

class CaseEvaluationResult(BaseModel):
    result_id: str
    evaluation_id: str
    case_id: str
    status: EvaluationStatusEnum
    functional_score: float = 0.0
    code_quality_score: float = 0.0
    test_score: float = 0.0
    security_score: float = 0.0
    trajectory_score: float = 0.0
    reliability_score: float = 0.0
    cost_score: float = 0.0
    latency_score: float = 0.0
    overall_score: float = 0.0
    critical_failures: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: float = 0.0
    tokens_used: int = 0
    estimated_cost_usd: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class EvaluationSummaryMetrics(BaseModel):
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    needs_review_cases: int = 0
    pass_rate_pct: float = 0.0
    avg_functional_score: float = 0.0
    avg_code_quality_score: float = 0.0
    avg_test_score: float = 0.0
    avg_security_score: float = 0.0
    avg_trajectory_score: float = 0.0
    avg_reliability_score: float = 0.0
    avg_cost_score: float = 0.0
    avg_latency_score: float = 0.0
    avg_overall_score: float = 0.0
    total_critical_failures: int = 0
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    total_duration_ms: float = 0.0

class EvaluationRun(BaseModel):
    evaluation_id: str
    dataset_id: str
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_version: str = "v1.16.0"
    prompt_version: str = "v1.0.0"
    model_provider: str = "ollama"
    model_name: str = "llama3:latest"
    evaluation_type: EvaluationTypeEnum = EvaluationTypeEnum.END_TO_END
    status: EvaluationStatusEnum = EvaluationStatusEnum.PENDING
    overall_score: float = 0.0
    passed: bool = False
    weights: EvaluationScoreWeights = Field(default_factory=EvaluationScoreWeights)
    thresholds: EvaluationPassThresholds = Field(default_factory=EvaluationPassThresholds)
    summary: EvaluationSummaryMetrics = Field(default_factory=EvaluationSummaryMetrics)
    results: List[CaseEvaluationResult] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

class EvaluationRunRequest(BaseModel):
    dataset_id: str
    project_id: Optional[str] = "proj_eval_default"
    model: Optional[str] = "llama3:latest"
    provider: Optional[str] = "ollama"
    evaluation_type: Optional[EvaluationTypeEnum] = EvaluationTypeEnum.END_TO_END
    case_ids: Optional[List[str]] = None
    mock_mode: bool = False
    weights: Optional[EvaluationScoreWeights] = None
    thresholds: Optional[EvaluationPassThresholds] = None

class RegressionComparison(BaseModel):
    comparison_id: str
    baseline_evaluation_id: str
    current_evaluation_id: str
    dataset_id: str
    baseline_score: float
    current_score: float
    delta_score: float
    regression_detected: bool
    block_release: bool
    reasons: List[str] = Field(default_factory=list)
    score_breakdown_delta: Dict[str, float] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ModelLeaderboardEntry(BaseModel):
    model_name: str
    provider_name: str
    dataset_id: str
    dataset_version: str
    evaluations_count: int = 0
    avg_functional: float = 0.0
    avg_code_quality: float = 0.0
    avg_security: float = 0.0
    avg_testing: float = 0.0
    avg_trajectory: float = 0.0
    avg_reliability: float = 0.0
    avg_overall_score: float = 0.0
    avg_cost_usd: float = 0.0
    avg_latency_ms: float = 0.0
    rank: int = 1

class ModelLeaderboard(BaseModel):
    dataset_id: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    entries: List[ModelLeaderboardEntry] = Field(default_factory=list)

class HumanEvaluationRecord(BaseModel):
    human_eval_id: str
    evaluation_id: str
    case_id: Optional[str] = None
    reviewer_id: str
    reviewer_role: str
    understanding_score: float = Field(ge=0, le=100)
    architecture_score: float = Field(ge=0, le=100)
    code_quality_score: float = Field(ge=0, le=100)
    maintainability_score: float = Field(ge=0, le=100)
    documentation_score: float = Field(ge=0, le=100)
    developer_experience_score: float = Field(ge=0, le=100)
    overall_usefulness_score: float = Field(ge=0, le=100)
    comments: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class LLMJudgeResult(BaseModel):
    score: float = Field(ge=0, le=100)
    criteria_scores: Dict[str, float] = Field(default_factory=dict)
    critical_failures: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    recommendation: str = "PASS"
    reasoning: str = ""

from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone

# 1. Project Information
class ProjectInformation(BaseModel):
    project_name: str = Field(..., description="Human-readable project name")
    project_slug: str = Field(..., description="kebab-case identifier")
    version: str = Field(default="1.0.0", description="Semantic version string")
    summary: str = Field(..., description="High-level executive summary")
    domain: str = Field(..., description="Industry domain e.g. E-Commerce / FinTech")
    target_environment: Literal["development", "staging", "production"] = "production"

# 2. Recommended Technology Stack
class ToolingSpec(BaseModel):
    linter: str = "Ruff"
    formatter: str = "Black"
    test_runner: str = "Pytest"
    container_runtime: str = "Docker & Docker Compose"

class RecommendedTechStack(BaseModel):
    core_language: str = Field(default="Python 3.11+")
    backend_framework: str = Field(default="FastAPI")
    database: str = Field(default="PostgreSQL 16 with SQLAlchemy 2.0 & Alembic")
    cache_layer: str = Field(default="Redis 7.0 (Session & Rate Limiting)")
    auth_mechanism: str = Field(default="JWT (HMAC-SHA256) with Refresh Tokens")
    api_protocol: Literal["REST", "GraphQL", "gRPC"] = "REST"
    tooling: ToolingSpec = Field(default_factory=ToolingSpec)

# 3. Architecture Recommendation
class ArchitectureRecommendation(BaseModel):
    pattern: str = Field(default="Modular Monolith with Clean Architecture & Domain-Driven Design")
    database_design_strategy: str = Field(default="Third Normal Form (3NF) relational tables with foreign keys and index optimization")
    api_design_standard: str = Field(default="OpenAPI 3.1 compliant RESTful endpoints with standard HTTP status codes")
    directory_structure_blueprint: List[str] = Field(default_factory=lambda: [
        "app/core/", "app/models/", "app/schemas/", "app/services/", "app/api/v1/", "tests/"
    ])
    bounded_contexts: List[str] = Field(default_factory=list)

# 4. Requirements Specification
class FunctionalReq(BaseModel):
    id: str = Field(..., description="e.g. FR-AUTH-01")
    module: str = Field(..., description="Target bounded context module")
    title: str = Field(..., description="Concise requirement title")
    user_story: str = Field(..., description="As a <actor>, I want <action> so that <benefit>")
    business_rules: List[str] = Field(default_factory=list)

class NonFunctionalReq(BaseModel):
    id: str = Field(..., description="e.g. NFR-PERF-01")
    category: Literal["SECURITY", "PERFORMANCE", "SCALABILITY", "RELIABILITY", "MAINTAINABILITY"]
    constraint: str = Field(..., description="Technical constraint description")
    target_metric: Optional[str] = Field(default=None, description="e.g. p99 latency < 200ms at 1000 RPS")

class RequirementsContainer(BaseModel):
    functional: List[FunctionalReq] = Field(default_factory=list)
    non_functional: List[NonFunctionalReq] = Field(default_factory=list)

# 5. Assumptions & Clarifications
class AssumptionItem(BaseModel):
    id: str = Field(..., description="e.g. ASM-01")
    category: Literal["BUSINESS", "TECHNICAL", "INFRASTRUCTURE", "SECURITY"]
    assumption_text: str
    rationale: str

class ClarificationItem(BaseModel):
    ambiguity_id: str
    question: str
    severity: Literal["BLOCKING", "NON_BLOCKING"]
    assumed_default: str

# 6. Features / Modules
class FeatureSpec(BaseModel):
    feature_id: str = Field(..., description="e.g. FEAT-AUTH-01")
    name: str
    purpose: str
    database_tables: List[str] = Field(default_factory=list)
    api_endpoints: List[str] = Field(default_factory=list)
    dependent_features: List[str] = Field(default_factory=list)

# 7. Atomic Tasks & DAG
class TargetFiles(BaseModel):
    create: List[str] = Field(default_factory=list)
    modify: List[str] = Field(default_factory=list)

class AtomicTask(BaseModel):
    task_id: str = Field(..., description="e.g. TASK-001")
    title: str
    feature_id: str
    task_type: Literal["SCHEMA", "CRUD", "SERVICE", "ENDPOINT", "INTEGRATION", "TEST", "CONFIG"]
    priority: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    complexity: Literal["XS", "S", "M", "L", "XL"]
    estimated_hours: float = Field(default=1.0, ge=0.5, le=12.0)
    upstream_dependencies: List[str] = Field(default_factory=list)
    target_files: TargetFiles = Field(default_factory=TargetFiles)
    acceptance_criteria: List[str] = Field(default_factory=list, min_length=2)

# 8. Risks & Mitigations
class RiskItem(BaseModel):
    risk_id: str = Field(..., description="e.g. RISK-01")
    category: Literal["TECHNICAL", "SECURITY", "INTEGRATION", "PERFORMANCE", "OPERATIONAL"]
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    likelihood: Literal["HIGH", "MEDIUM", "LOW"]
    description: str
    mitigation_strategy: str

# 9. Testing Strategy
class TestingStrategy(BaseModel):
    unit_testing: str = Field(default="Isolated service and utility logic testing with mock repositories")
    integration_testing: str = Field(default="Database CRUD and API endpoint tests using TestClient and ephemeral PostgreSQL test DB")
    e2e_testing: str = Field(default="Complete checkout flow simulation (User Auth -> Cart -> Order -> Payment Webhook)")
    target_code_coverage_pct: int = Field(default=85, ge=70, le=100)
    test_frameworks: List[str] = Field(default_factory=lambda: ["pytest", "pytest-asyncio", "httpx"])

# 10. Deployment Recommendation
class DeploymentRecommendation(BaseModel):
    containerization: str = Field(default="Multi-stage Dockerfile with non-root security context")
    orchestration: str = Field(default="Docker Compose for local dev; Kubernetes / ECS for production")
    cicd_pipeline: str = Field(default="GitHub Actions workflow running Ruff linting, Pytest suite, and Docker image build")
    observability: str = Field(default="Structured JSON logging, Prometheus metrics endpoint, OpenTelemetry distributed tracing")
    scaling_strategy: str = Field(default="Stateless horizontal scaling of FastAPI worker pods with Redis caching")

# 11. Execution Metadata & Phases
class PlanPhase(BaseModel):
    phase_number: int
    phase_name: str
    description: str
    task_ids: List[str]

class ExecutionMetadata(BaseModel):
    total_estimated_hours: float
    critical_path: List[str]
    total_phases: int
    phases: List[PlanPhase]

# 12. Master Structured Software Development Plan
class StructuredSoftwareDevelopmentPlan(BaseModel):
    project_information: ProjectInformation
    recommended_technology_stack: RecommendedTechStack
    architecture_recommendation: ArchitectureRecommendation
    requirements: RequirementsContainer
    assumptions: List[AssumptionItem]
    features: List[FeatureSpec]
    tasks: List[AtomicTask]
    risks: List[RiskItem]
    testing_strategy: TestingStrategy
    deployment_recommendation: DeploymentRecommendation
    execution_metadata: ExecutionMetadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# 13. Human Approval State
class HumanApprovalState(BaseModel):
    status: Literal["PENDING", "APPROVED", "REJECTED"] = "PENDING"
    approved_by: Optional[str] = None
    feedback: Optional[str] = None
    timestamp: Optional[str] = None

# 14. API Request/Response DTOs
class PlannerInputRequest(BaseModel):
    user_id: Optional[str] = "user_default_01"
    project_id: Optional[str] = "proj_default_01"
    task_id: Optional[str] = None
    raw_requirement: str = Field(
        ...,
        min_length=10,
        description="Software requirement description",
        json_schema_extra={"example": "Build an e-commerce application with authentication, products, shopping cart, orders and payment."}
    )
    target_tech_stack: Optional[Dict[str, str]] = None
    project_type: Optional[Literal["greenfield", "brownfield"]] = "greenfield"
    max_tasks: Optional[int] = 50

class PlannerResponse(BaseModel):
    task_id: str
    session_id: str
    current_agent: str
    execution_status: str
    plan: Optional[StructuredSoftwareDevelopmentPlan] = None
    clarifications: Optional[List[ClarificationItem]] = None
    human_approval: Optional[HumanApprovalState] = None
    errors: Optional[List[str]] = None
    retry_count: int = 0

from enum import Enum
from typing import List, Dict, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from app.schemas.plan import (
    StructuredSoftwareDevelopmentPlan,
    ProjectInformation,
    FunctionalReq,
    NonFunctionalReq,
    FeatureSpec,
    AtomicTask,
    RecommendedTechStack
)

# 1. Enums
class ArchitecturePatternEnum(str, Enum):
    MODULAR_MONOLITH = "Modular Monolith with Clean Architecture & Domain-Driven Design"
    MICROSERVICES = "Event-Driven Microservices Architecture"
    SERVERLESS = "Stateless Serverless Architecture"
    LAYERED = "Classic N-Tier Layered Architecture"
    HEXAGONAL = "Hexagonal Architecture (Ports & Adapters)"

class ComponentTypeEnum(str, Enum):
    MODULE = "MODULE"
    SERVICE = "SERVICE"
    GATEWAY = "GATEWAY"
    REPOSITORY = "REPOSITORY"
    QUEUE_WORKER = "QUEUE_WORKER"
    CACHE_LAYER = "CACHE_LAYER"

class DatabaseEngineEnum(str, Enum):
    POSTGRESQL = "PostgreSQL 16"
    MYSQL = "MySQL 8.0"
    SQLITE = "SQLite 3"
    MONGODB = "MongoDB 7.0"
    REDIS = "Redis 7.0"

class HTTPMethodEnum(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"

class SecurityLevelEnum(str, Enum):
    PUBLIC = "PUBLIC"
    AUTHENTICATED = "AUTHENTICATED"
    RBAC_ADMIN = "RBAC_ADMIN"
    RBAC_STAFF = "RBAC_STAFF"

class ApprovalStatusEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVISION_REQUIRED = "REVISION_REQUIRED"

# 2. Components & Relationships
class ComponentRelationship(BaseModel):
    source_component: str = Field(..., description="Name of initiating component")
    target_component: str = Field(..., description="Name of receiving component")
    relationship_type: str = Field(..., description="DEPENDS_ON, INVOKES_ASYNC, QUERIES, SENDS_EVENT")
    communication_protocol: str = Field(default="IN_PROCESS_CALL", description="Protocol used")

class ArchitectureComponent(BaseModel):
    component_id: str = Field(..., description="Unique ID e.g. COMP-AUTH-01")
    name: str = Field(..., description="Component name")
    component_type: ComponentTypeEnum = Field(default=ComponentTypeEnum.MODULE)
    responsibility: str = Field(..., description="Primary architectural responsibility")
    module_path: str = Field(..., description="Target file/directory e.g. app/modules/customers/")
    related_features: List[str] = Field(default_factory=list, description="IDs of linked features")
    dependencies: List[str] = Field(default_factory=list, description="IDs of dependent components")

# 3. Database Architecture
class DatabaseField(BaseModel):
    name: str = Field(..., description="Field name in database")
    data_type: str = Field(..., description="PostgreSQL type e.g. UUID, VARCHAR(255), INTEGER, TIMESTAMP")
    is_primary_key: bool = False
    is_nullable: bool = False
    is_unique: bool = False
    default_value: Optional[str] = None
    description: str = Field(..., description="Purpose of field")

class DatabaseRelationship(BaseModel):
    target_entity: str = Field(..., description="Target table/entity name")
    relationship_type: str = Field(..., description="ONE_TO_ONE, ONE_TO_MANY, MANY_TO_MANY")
    foreign_key_column: str = Field(..., description="Column holding FK")
    on_delete: str = Field(default="CASCADE", description="CASCADE, SET NULL, RESTRICT")

class DatabaseIndex(BaseModel):
    index_name: str
    columns: List[str]
    is_unique: bool = False
    index_type: str = "BTREE"

class DatabaseEntity(BaseModel):
    entity_id: str = Field(..., description="ID e.g. ENT-01")
    table_name: str = Field(..., description="SQL table name e.g. customers")
    description: str
    fields: List[DatabaseField] = Field(default_factory=list)
    relationships: List[DatabaseRelationship] = Field(default_factory=list)
    indexes: List[DatabaseIndex] = Field(default_factory=list)

class DatabaseDesign(BaseModel):
    database_engine: DatabaseEngineEnum = DatabaseEngineEnum.POSTGRESQL
    orm_framework: str = "SQLAlchemy 2.0 (Async) with Alembic"
    migration_strategy: str = "Alembic Versioned Migrations"
    normalization_level: str = "3NF (Third Normal Form)"
    entities: List[DatabaseEntity] = Field(default_factory=list)

# 4. API Architecture
class APIParameter(BaseModel):
    name: str
    location: Literal["path", "query", "header", "cookie"] = "query"
    data_type: str
    required: bool = True
    description: str

class APIRequestModel(BaseModel):
    model_name: str
    fields: Dict[str, str] = Field(default_factory=dict)
    example_payload: Dict[str, Any] = Field(default_factory=dict)

class APIResponseModel(BaseModel):
    status_code: int = 200
    model_name: str
    fields: Dict[str, str] = Field(default_factory=dict)

class APIEndpoint(BaseModel):
    endpoint_id: str = Field(..., description="e.g. API-CUST-01")
    path: str = Field(..., description="e.g. /api/v1/customers")
    method: HTTPMethodEnum = HTTPMethodEnum.GET
    summary: str
    module: str
    security_level: SecurityLevelEnum = SecurityLevelEnum.AUTHENTICATED
    parameters: List[APIParameter] = Field(default_factory=list)
    request_model: Optional[APIRequestModel] = None
    response_models: List[APIResponseModel] = Field(default_factory=list)

class APIDesign(BaseModel):
    api_protocol: str = "REST (FastAPI OpenAPI 3.1)"
    base_prefix: str = "/api/v1"
    endpoints: List[APIEndpoint] = Field(default_factory=list)

# 5. Security & Access Control
class SecurityControl(BaseModel):
    control_id: str
    category: str = Field(..., description="ENCRYPTION, AUTHENTICATION, AUTHORIZATION, NETWORK")
    description: str
    mitigation: str

class AuthenticationDesign(BaseModel):
    mechanism: str = "JWT (HMAC-SHA256) with Passlib Bcrypt Hashing"
    access_token_expiry_minutes: int = 30
    refresh_token_expiry_days: int = 7
    storage_mechanism: str = "HttpOnly Secure Cookie + Authorization Header"

class AuthorizationDesign(BaseModel):
    model: str = "Role-Based Access Control (RBAC)"
    roles: List[str] = Field(default_factory=lambda: ["ADMIN", "STAFF", "CUSTOMER", "GUEST"])
    role_permissions_matrix: Dict[str, List[str]] = Field(default_factory=dict)

class SecurityDesign(BaseModel):
    authentication: AuthenticationDesign = Field(default_factory=AuthenticationDesign)
    authorization: AuthorizationDesign = Field(default_factory=AuthorizationDesign)
    tls_version: str = "TLS 1.3 Strict"
    cors_policy: str = "Explicit Allowed Origins with Credentials"
    security_controls: List[SecurityControl] = Field(default_factory=list)

# 6. Caching & Background Processing
class CachingStrategy(BaseModel):
    cache_engine: str = "Redis 7.0"
    session_cache_ttl_seconds: int = 1209600 # 14 days
    query_cache_ttl_seconds: int = 300 # 5 min
    invalidation_strategy: str = "Key pattern invalidation on entity mutation"

class BackgroundProcessing(BaseModel):
    queue_engine: str = "Redis Celery Worker"
    concurrency_model: str = "Asyncio Task Queues with Worker Isolation"
    job_retry_limit: int = 3

# 7. Testing & Deployment Strategy
class TestStrategy(BaseModel):
    __test__ = False
    test_framework: str = "Pytest 8.x with pytest-asyncio and httpx TestClient"
    unit_testing: str = "Isolated service tests with Mock Repositories"
    integration_testing: str = "Ephemeral SQLite/PostgreSQL Test DB for API endpoints"
    target_coverage_pct: int = 85

class DeploymentStrategy(BaseModel):
    containerization: str = "Multi-Stage Dockerfile (Python 3.12-slim)"
    cicd_pipeline: str = "GitHub Actions (Lint, Test, Docker Build)"
    observability: str = "Structured JSON logs with correlation IDs and OpenTelemetry tracing"

# 8. High-Level & Low-Level Design Documents
class HighLevelDesign(BaseModel):
    system_overview: str
    c4_context_diagram_description: str
    data_flow_overview: str
    external_integrations: List[str] = Field(default_factory=list)

class LowLevelDesign(BaseModel):
    package_structure: str
    service_interface_contracts: List[str] = Field(default_factory=list)
    error_handling_strategy: str = "Global FastAPI Exception Handlers with RFC 7807 Problem Details"

class FolderStructureBlueprint(BaseModel):
    root_directory: str = "app/"
    directory_tree: List[str] = Field(default_factory=list)

# 9. Architecture Decisions, Risks & Tradeoffs
class ArchitectureDecision(BaseModel):
    adr_id: str
    title: str
    status: Literal["ACCEPTED", "PROPOSED", "DEPRECATED"] = "ACCEPTED"
    context: str
    decision: str
    consequences: str

class ArchitectureRisk(BaseModel):
    risk_id: str
    severity: str
    description: str
    mitigation_strategy: str

class ArchitectureTradeoff(BaseModel):
    tradeoff_id: str
    aspect: str
    chosen_approach: str
    rejected_alternative: str
    rationale: str

# 10. Requirement Traceability Matrix & Validation Result
class RequirementTraceabilityItem(BaseModel):
    req_id: str = Field(..., description="Planner FR ID e.g. FR-CUST-01")
    req_title: str
    feature_name: str
    architecture_component: str
    database_entity: str
    api_endpoint: str
    test_strategy: str

class ValidationResult(BaseModel):
    validation_status: Literal["VALID", "WARNINGS", "FAILED"] = "VALID"
    validation_score: int = Field(default=100, ge=0, le=100)
    requirement_coverage_pct: float = Field(default=100.0, ge=0.0, le=100.0)
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)
    traceability_matrix: List[RequirementTraceabilityItem] = Field(default_factory=list)

class HumanApproval(BaseModel):
    status: ApprovalStatusEnum = ApprovalStatusEnum.PENDING
    approved_by: str = "Awaiting_Human_Review"
    comments: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# 11. Master Architecture Schema
class StructuredSoftwareArchitecture(BaseModel):
    project_information: ProjectInformation
    architecture_pattern: ArchitecturePatternEnum = ArchitecturePatternEnum.MODULAR_MONOLITH
    architecture_overview: str
    components: List[ArchitectureComponent] = Field(default_factory=list)
    component_relationships: List[ComponentRelationship] = Field(default_factory=list)
    database_design: DatabaseDesign = Field(default_factory=DatabaseDesign)
    api_design: APIDesign = Field(default_factory=APIDesign)
    security_design: SecurityDesign = Field(default_factory=SecurityDesign)
    caching_strategy: CachingStrategy = Field(default_factory=CachingStrategy)
    background_processing: BackgroundProcessing = Field(default_factory=BackgroundProcessing)
    testing_design: TestStrategy = Field(default_factory=TestStrategy)
    deployment_design: DeploymentStrategy = Field(default_factory=DeploymentStrategy)
    high_level_design: HighLevelDesign
    low_level_design: LowLevelDesign
    folder_structure: FolderStructureBlueprint
    architecture_decisions: List[ArchitectureDecision] = Field(default_factory=list)
    risks: List[ArchitectureRisk] = Field(default_factory=list)
    tradeoffs: List[ArchitectureTradeoff] = Field(default_factory=list)
    validation_results: ValidationResult = Field(default_factory=ValidationResult)
    human_approval: HumanApproval = Field(default_factory=HumanApproval)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# 12. API Requests & Responses
class ArchitectInputRequest(BaseModel):
    user_id: Optional[str] = "user_pramod_01"
    project_id: Optional[str] = "project_default_01"
    planner_task_id: Optional[str] = None
    planner_output: Optional[StructuredSoftwareDevelopmentPlan] = None

class ArchitectResponse(BaseModel):
    architect_task_id: str
    planner_task_id: Optional[str] = None
    project_id: str
    architecture_status: str
    human_approval: HumanApproval
    architecture: Optional[StructuredSoftwareArchitecture] = None
    validation_results: Optional[ValidationResult] = None
    errors: List[str] = Field(default_factory=list)
    retry_count: int = 0

class ApprovalActionRequest(BaseModel):
    reviewer_name: str = "Lead_Architect"
    notes: Optional[str] = None

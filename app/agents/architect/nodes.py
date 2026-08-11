import uuid
import re
from typing import Dict, Any, List
from datetime import datetime, timezone
from app.agents.architect.state import ArchitectState
from app.schemas.architecture import (
    ArchitecturePatternEnum,
    ComponentTypeEnum,
    DatabaseEngineEnum,
    HTTPMethodEnum,
    SecurityLevelEnum,
    ApprovalStatusEnum,
    ComponentRelationship,
    ArchitectureComponent,
    DatabaseField,
    DatabaseRelationship,
    DatabaseIndex,
    DatabaseEntity,
    DatabaseDesign,
    APIParameter,
    APIRequestModel,
    APIResponseModel,
    APIEndpoint,
    APIDesign,
    SecurityControl,
    AuthenticationDesign,
    AuthorizationDesign,
    SecurityDesign,
    CachingStrategy,
    BackgroundProcessing,
    TestStrategy,
    DeploymentStrategy,
    HighLevelDesign,
    LowLevelDesign,
    FolderStructureBlueprint,
    ArchitectureDecision,
    ArchitectureRisk,
    ArchitectureTradeoff,
    ValidationResult,
    HumanApproval,
    StructuredSoftwareArchitecture
)
from app.schemas.plan import ProjectInformation
from app.agents.architect.validator import architecture_validator
from app.core.logging import logger
from app.services.storage import storage_service

# Helper function for dynamic domain naming
def _clean_slug(text: str) -> str:
    return re.sub(r'[^a-zA-Z0-9]+', '_', text.lower()).strip('_')

# 1. validate_planner_output
async def validate_planner_output_node(state: ArchitectState) -> Dict[str, Any]:
    arch_task_id = state.get("architect_task_id") or str(uuid.uuid4())
    planner_output = state.get("planner_output")
    
    if not planner_output:
        planner_task_id = state.get("planner_task_id")
        if planner_task_id:
            planner_output = storage_service.get_plan(planner_task_id)
            
    if not planner_output:
        logger.error("Architect Agent received empty Planner output.")
        return {
            "architect_task_id": arch_task_id,
            "architecture_status": "PLANNER_OUTPUT_MISSING",
            "errors": ["Planner output could not be resolved from state or task store."]
        }
        
    proj_info = planner_output.project_information
    frs = planner_output.requirements.functional
    nfrs = planner_output.requirements.non_functional
    features = planner_output.features
    tasks = planner_output.tasks
    
    logger.info(f"Ingested Plan for: {proj_info.project_name} ({len(frs)} FRs, {len(tasks)} tasks)")
    
    return {
        "architect_task_id": arch_task_id,
        "planner_output": planner_output,
        "project_information": proj_info,
        "functional_requirements": frs,
        "non_functional_requirements": nfrs,
        "features": features,
        "tasks": tasks,
        "technology_stack": planner_output.recommended_technology_stack,
        "current_step": "validate_planner_output",
        "architecture_status": "PLANNER_VALIDATED",
        "retry_count": state.get("retry_count", 0),
        "errors": []
    }

# 2. analyze_requirements
async def analyze_requirements_node(state: ArchitectState) -> Dict[str, Any]:
    proj_info = state.get("project_information")
    frs = state.get("functional_requirements", [])
    
    plan = state.get("planner_output")
    assumptions = getattr(plan, "assumptions", []) if plan else []
    clarifications = getattr(plan, "clarifications", []) if plan else state.get("clarifications", [])
    
    return {
        "current_step": "analyze_requirements",
        "assumptions": assumptions,
        "clarifications": clarifications,
        "architecture_status": "REQUIREMENTS_ANALYZED"
    }

# 3. select_architecture
async def select_architecture_node(state: ArchitectState) -> Dict[str, Any]:
    proj_info = state.get("project_information")
    name = proj_info.project_name if proj_info else "Application"
    
    pattern = ArchitecturePatternEnum.MODULAR_MONOLITH
    overview = (
        f"The {name} is designed as a Modular Monolith leveraging Clean Architecture and Domain-Driven Design (DDD). "
        f"Domain modules maintain clear Bounded Contexts with independent services, repositories, and API routers, "
        f"enabling high maintainability and straightforward future migration to event-driven microservices if needed."
    )
    
    adrs = [
        ArchitectureDecision(
            adr_id="ADR-001",
            title="Adopt Modular Monolith with Clean Architecture",
            status="ACCEPTED",
            context=f"The system needs robust maintainability, high developer velocity, and zero distributed transaction overhead.",
            decision="Structure application modules with strict boundary isolation and dependency inversion.",
            consequences="Simplified deployment and testing; cross-module queries must go through service contracts."
        ),
        ArchitectureDecision(
            adr_id="ADR-002",
            title="Use PostgreSQL 16 as Relational Source of Truth",
            status="ACCEPTED",
            context="Domain transactions require ACID guarantees across core entities.",
            decision="Utilize PostgreSQL 16 with SQLAlchemy 2.0 async ORM and Alembic migrations.",
            consequences="Guaranteed referential integrity and transaction rollbacks on failure."
        )
    ]
    
    tradeoffs = [
        ArchitectureTradeoff(
            tradeoff_id="TRD-01",
            aspect="Monolith vs Microservices",
            chosen_approach="Modular Monolith with Domain Boundaries",
            rejected_alternative="Distributed Microservices",
            rationale="Eliminates network serialization latency, distributed saga complexity, and multiple deployment overheads."
        )
    ]
    
    return {
        "current_step": "select_architecture",
        "architecture_pattern": pattern,
        "architecture_overview": overview,
        "architecture_decisions": adrs,
        "tradeoffs": tradeoffs,
        "architecture_status": "ARCHITECTURE_SELECTED"
    }

# 4. design_components
async def design_components_node(state: ArchitectState) -> Dict[str, Any]:
    frs = state.get("functional_requirements", [])
    components: List[ArchitectureComponent] = []
    relationships: List[ComponentRelationship] = []
    
    for idx, fr in enumerate(frs, start=1):
        slug = _clean_slug(fr.module)
        comp_id = f"COMP-{slug.upper()[:4]}-{idx:02d}"
        components.append(
            ArchitectureComponent(
                component_id=comp_id,
                name=f"{fr.module} Module",
                component_type=ComponentTypeEnum.MODULE,
                responsibility=f"Encapsulates domain logic, entities, services, and API controllers for {fr.module}.",
                module_path=f"app/modules/{slug}/",
                related_features=[fr.id],
                dependencies=[components[0].component_id] if idx > 1 else []
            )
        )
        if idx > 1:
            relationships.append(
                ComponentRelationship(
                    source_component=f"{fr.module} Module",
                    target_component=components[0].name,
                    relationship_type="DEPENDS_ON",
                    communication_protocol="IN_PROCESS_CALL"
                )
            )
            
    data_flow = (
        "Client Request -> FastAPI CORS/Auth Middleware -> Domain APIRouter -> "
        "Service Layer Validation -> Repository CRUD Query -> PostgreSQL Database / Redis Cache."
    )
    
    return {
        "current_step": "design_components",
        "components": components,
        "component_relationships": relationships,
        "data_flow": data_flow,
        "architecture_status": "COMPONENTS_DESIGNED"
    }

# 5. design_database
async def design_database_node(state: ArchitectState) -> Dict[str, Any]:
    frs = state.get("functional_requirements", [])
    entities: List[DatabaseEntity] = []
    
    for idx, fr in enumerate(frs, start=1):
        slug = _clean_slug(fr.module)
        table_name = f"{slug}_records"
        
        fields = [
            DatabaseField(name="id", data_type="UUID", is_primary_key=True, is_nullable=False, description="Primary unique entity identifier"),
            DatabaseField(name="name", data_type="VARCHAR(255)", is_nullable=False, description=f"Name or title of the {fr.module} entity"),
            DatabaseField(name="status", data_type="VARCHAR(50)", is_nullable=False, default_value="'ACTIVE'", description="Operational status lifecycle flag"),
            DatabaseField(name="metadata_payload", data_type="JSONB", is_nullable=True, description="Flexible unstructured domain attributes"),
            DatabaseField(name="created_at", data_type="TIMESTAMP WITH TIME ZONE", is_nullable=False, default_value="NOW()", description="Creation timestamp"),
            DatabaseField(name="updated_at", data_type="TIMESTAMP WITH TIME ZONE", is_nullable=False, default_value="NOW()", description="Last update timestamp")
        ]
        
        indexes = [
            DatabaseIndex(index_name=f"idx_{slug}_status", columns=["status"], is_unique=False),
            DatabaseIndex(index_name=f"idx_{slug}_created_at", columns=["created_at"], is_unique=False)
        ]
        
        entities.append(
            DatabaseEntity(
                entity_id=f"ENT-{slug.upper()[:4]}-{idx:02d}",
                table_name=table_name,
                description=f"Relational storage for {fr.module} records and audit history.",
                fields=fields,
                indexes=indexes
            )
        )
        
    db_design = DatabaseDesign(
        database_engine=DatabaseEngineEnum.POSTGRESQL,
        orm_framework="SQLAlchemy 2.0 Async with Alembic",
        migration_strategy="Alembic Versioned DDL Migrations",
        normalization_level="3NF (Third Normal Form)",
        entities=entities
    )
    
    return {
        "current_step": "design_database",
        "database_design": db_design,
        "architecture_status": "DATABASE_DESIGNED"
    }

# 6. design_api
async def design_api_node(state: ArchitectState) -> Dict[str, Any]:
    frs = state.get("functional_requirements", [])
    endpoints: List[APIEndpoint] = []
    
    for idx, fr in enumerate(frs, start=1):
        slug = _clean_slug(fr.module)
        base_path = f"/api/v1/{slug.replace('_', '-')}"
        
        # GET List
        endpoints.append(
            APIEndpoint(
                endpoint_id=f"API-{slug.upper()[:4]}-01",
                path=base_path,
                method=HTTPMethodEnum.GET,
                summary=f"List {fr.module} records with pagination",
                module=fr.module,
                security_level=SecurityLevelEnum.AUTHENTICATED,
                parameters=[
                    APIParameter(name="page", location="query", data_type="int", required=False, description="Page number"),
                    APIParameter(name="limit", location="query", data_type="int", required=False, description="Page size limit")
                ],
                response_models=[APIResponseModel(status_code=200, model_name=f"{fr.module.replace(' ', '')}ListResponse")]
            )
        )
        # POST Create
        endpoints.append(
            APIEndpoint(
                endpoint_id=f"API-{slug.upper()[:4]}-02",
                path=base_path,
                method=HTTPMethodEnum.POST,
                summary=f"Create a new {fr.module} record",
                module=fr.module,
                security_level=SecurityLevelEnum.AUTHENTICATED,
                request_model=APIRequestModel(
                    model_name=f"{fr.module.replace(' ', '')}CreateRequest",
                    fields={"name": "str", "status": "str"},
                    example_payload={"name": f"Sample {fr.module}", "status": "ACTIVE"}
                ),
                response_models=[APIResponseModel(status_code=201, model_name=f"{fr.module.replace(' ', '')}DetailResponse")]
            )
        )
        
    api_design = APIDesign(base_prefix="/api/v1", endpoints=endpoints)
    
    return {
        "current_step": "design_api",
        "api_design": api_design,
        "architecture_status": "API_DESIGNED"
    }

# 7. design_security
async def design_security_node(state: ArchitectState) -> Dict[str, Any]:
    sec_design = SecurityDesign(
        authentication=AuthenticationDesign(
            mechanism="JWT (HMAC-SHA256) with Passlib Bcrypt Hashing",
            access_token_expiry_minutes=30,
            refresh_token_expiry_days=7
        ),
        authorization=AuthorizationDesign(
            model="Role-Based Access Control (RBAC)",
            roles=["ADMIN", "STAFF", "CUSTOMER", "GUEST"],
            role_permissions_matrix={
                "ADMIN": ["*:*"],
                "STAFF": ["read:*", "write:operations"],
                "CUSTOMER": ["read:own", "write:own"],
                "GUEST": ["read:public"]
            }
        ),
        security_controls=[
            SecurityControl(control_id="SEC-01", category="ENCRYPTION", description="TLS 1.3 enforced on all external endpoints", mitigation="Strict HSTS headers"),
            SecurityControl(control_id="SEC-02", category="AUTHORIZATION", description="Granular RBAC dependencies on FastAPI routes", mitigation="403 Forbidden on role mismatch"),
            SecurityControl(control_id="SEC-03", category="SECRETS", description="Pydantic BaseSettings loading secrets from environment", mitigation="Zero plaintext credentials")
        ]
    )
    
    return {
        "current_step": "design_security",
        "security_design": sec_design,
        "architecture_status": "SECURITY_DESIGNED"
    }

# 8. design_testing
async def design_testing_node(state: ArchitectState) -> Dict[str, Any]:
    test_design = TestStrategy(
        test_framework="Pytest 8.x with pytest-asyncio and httpx TestClient",
        unit_testing="Unit test coverage for domain services, models, and helper utilities with mock DB",
        integration_testing="API endpoint testing with ephemeral SQLite/PostgreSQL Test DB and TestClient",
        target_coverage_pct=85
    )
    return {
        "current_step": "design_testing",
        "testing_design": test_design,
        "architecture_status": "TESTING_DESIGNED"
    }

# 9. design_deployment
async def design_deployment_node(state: ArchitectState) -> Dict[str, Any]:
    deploy_design = DeploymentStrategy(
        containerization="Multi-Stage Dockerfile (python:3.12-slim) with non-root security context",
        cicd_pipeline="GitHub Actions CI running Ruff linting, Pytest suite, and Docker Hub build",
        observability="Structured JSON logging with correlation IDs and OpenTelemetry Prometheus metrics"
    )
    return {
        "current_step": "design_deployment",
        "deployment_design": deploy_design,
        "architecture_status": "DEPLOYMENT_DESIGNED"
    }

# 10. generate_hld
async def generate_hld_node(state: ArchitectState) -> Dict[str, Any]:
    proj_info = state.get("project_information")
    name = proj_info.project_name if proj_info else "Application"
    
    hld = HighLevelDesign(
        system_overview=f"High-Level Architectural Design for {name}.",
        c4_context_diagram_description="[Client Apps] -> [FastAPI Gateway / Modular Monolith] -> [PostgreSQL 16 DB] & [Redis 7.0 Cache].",
        data_flow_overview="HTTP REST APIs process domain commands, enforce RBAC, mutate ACID relational tables, and invalidate Redis cache.",
        external_integrations=["Payment Gateway (Stripe)", "Transactional Notifications (Email/Webhooks)"]
    )
    return {
        "current_step": "generate_hld",
        "hld": hld,
        "architecture_status": "HLD_GENERATED"
    }

# 11. generate_lld
async def generate_lld_node(state: ArchitectState) -> Dict[str, Any]:
    frs = state.get("functional_requirements", [])
    
    tree = [
        "app/",
        "├── __init__.py",
        "├── main.py",
        "├── core/",
        "│   ├── config.py",
        "│   ├── security.py",
        "│   └── logging.py",
        "├── db/",
        "│   ├── session.py",
        "│   └── base.py",
        "├── modules/"
    ]
    for fr in frs:
        slug = _clean_slug(fr.module)
        tree.extend([
            f"│   ├── {slug}/",
            f"│   │   ├── models.py",
            f"│   │   ├── schemas.py",
            f"│   │   ├── service.py",
            f"│   │   └── router.py"
        ])
    tree.extend([
        "tests/",
        "├── conftest.py",
        "└── modules/"
    ])
    for fr in frs:
        slug = _clean_slug(fr.module)
        tree.append(f"    └── test_{slug}.py")
        
    folder_struct = FolderStructureBlueprint(root_directory="app/", directory_tree=tree)
    
    lld = LowLevelDesign(
        package_structure="Domain-driven modular packages with schemas, models, services, and routers.",
        service_interface_contracts=[f"{fr.module}Service CRUD and business transaction methods" for fr in frs],
        error_handling_strategy="RFC 7807 Problem Details via global FastAPI exception handlers."
    )
    
    return {
        "current_step": "generate_lld",
        "lld": lld,
        "folder_structure": folder_struct,
        "architecture_status": "LLD_GENERATED"
    }

# 12. validate_architecture
async def validate_architecture_node(state: ArchitectState) -> Dict[str, Any]:
    frs = state.get("functional_requirements", [])
    nfrs = state.get("non_functional_requirements", [])
    components = state.get("components", [])
    db_design = state.get("database_design", DatabaseDesign())
    api_design = state.get("api_design", APIDesign())
    sec_design = state.get("security_design", SecurityDesign())
    test_design = state.get("testing_design", TestStrategy())
    deploy_design = state.get("deployment_design", DeploymentStrategy())
    
    validation_res = architecture_validator.audit_architecture(
        functional_reqs=frs,
        non_functional_reqs=nfrs,
        components=components,
        db_design=db_design,
        api_design=api_design,
        security_design=sec_design,
        test_strategy=test_design,
        deployment_strategy=deploy_design
    )
    
    logger.info(f"Architecture Validation: Status={validation_res.validation_status}, Score={validation_res.validation_score}, Coverage={validation_res.requirement_coverage_pct}%")
    
    return {
        "current_step": "validate_architecture",
        "validation_results": validation_res,
        "architecture_status": "VALIDATED" if validation_res.validation_status != "FAILED" else "VALIDATION_FAILED"
    }

# 13. human_review
async def human_review_node(state: ArchitectState) -> Dict[str, Any]:
    approval = HumanApproval(
        status=ApprovalStatusEnum.PENDING,
        approved_by="Awaiting_Human_Review",
        comments="Architecture successfully generated and validated. Pending developer lead approval.",
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    return {
        "current_step": "human_review",
        "human_approval": approval,
        "architecture_status": "AWAITING_APPROVAL"
    }

# 14. persist_architecture
async def persist_architecture_node(state: ArchitectState) -> Dict[str, Any]:
    arch_task_id = state.get("architect_task_id", str(uuid.uuid4()))
    proj_info = state.get("project_information", ProjectInformation(project_name="Application", project_slug="app", summary="", domain=""))
    
    final_arch = StructuredSoftwareArchitecture(
        project_information=proj_info,
        architecture_pattern=state.get("architecture_pattern", ArchitecturePatternEnum.MODULAR_MONOLITH),
        architecture_overview=state.get("architecture_overview", ""),
        components=state.get("components", []),
        component_relationships=state.get("component_relationships", []),
        database_design=state.get("database_design", DatabaseDesign()),
        api_design=state.get("api_design", APIDesign()),
        security_design=state.get("security_design", SecurityDesign()),
        caching_strategy=state.get("caching_strategy", CachingStrategy()),
        background_processing=state.get("background_processing", BackgroundProcessing()),
        testing_design=state.get("testing_design", TestStrategy()),
        deployment_design=state.get("deployment_design", DeploymentStrategy()),
        high_level_design=state.get("hld", HighLevelDesign(system_overview="", c4_context_diagram_description="", data_flow_overview="")),
        low_level_design=state.get("lld", LowLevelDesign(package_structure="")),
        folder_structure=state.get("folder_structure", FolderStructureBlueprint()),
        architecture_decisions=state.get("architecture_decisions", []),
        risks=state.get("risks", []),
        tradeoffs=state.get("tradeoffs", []),
        validation_results=state.get("validation_results", ValidationResult()),
        human_approval=state.get("human_approval", HumanApproval())
    )
    
    storage_service.save_architecture(arch_task_id, final_arch)
    logger.info(f"Persisted Architecture Task ID: {arch_task_id}")
    
    return {
        "current_step": "persist_architecture",
        "final_architecture": final_arch,
        "architecture_status": "COMPLETED"
    }

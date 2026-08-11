import re
import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.agents.planner.state import PlannerState
from app.schemas.plan import (
    ProjectInformation,
    RecommendedTechStack,
    ArchitectureRecommendation,
    RequirementsContainer,
    FunctionalReq,
    NonFunctionalReq,
    AssumptionItem,
    ClarificationItem,
    FeatureSpec,
    AtomicTask,
    TargetFiles,
    RiskItem,
    TestingStrategy,
    DeploymentRecommendation,
    PlanPhase,
    ExecutionMetadata,
    StructuredSoftwareDevelopmentPlan,
    HumanApprovalState
)
from app.agents.planner.validator import validator
from app.core.logging import logger
from app.core.llm import llm_client
from app.agents.planner.prompts import (
    AMBIGUITY_SYSTEM_PROMPT,
    DECOMPOSITION_SYSTEM_PROMPT,
    MODULE_ARCHITECTURE_SYSTEM_PROMPT,
    TASK_DAG_SYSTEM_PROMPT,
    RISK_SYSTEM_PROMPT
)

# Helper schemas for intermediate node parsing
class AmbiguityLLMResult(BaseModel):
    clarifications: List[ClarificationItem] = Field(default_factory=list)
    assumptions: List[AssumptionItem] = Field(default_factory=list)
    is_blocked_on_clarification: bool = False

class DecomposeLLMResult(BaseModel):
    functional_requirements: List[FunctionalReq] = Field(default_factory=list)
    non_functional_requirements: List[NonFunctionalReq] = Field(default_factory=list)

class ArchitectureLLMResult(BaseModel):
    project_name: str
    project_slug: str
    domain: str
    summary: str
    recommended_tech_stack: RecommendedTechStack
    architecture_recommendation: ArchitectureRecommendation
    features: List[FeatureSpec] = Field(default_factory=list)

class TaskDagLLMResult(BaseModel):
    tasks: List[AtomicTask] = Field(default_factory=list)

class RiskLLMResult(BaseModel):
    risks: List[RiskItem] = Field(default_factory=list)
    testing_strategy: TestingStrategy
    deployment_recommendation: DeploymentRecommendation


def _extract_domain_and_features_from_text(raw_req: str):
    """
    Dynamic semantic extractor that parses modules and features directly from the user's requirement.
    Extracts custom modules (e.g. Hotel Management, Customer Registration, Room Booking, etc.)
    """
    clean_text = raw_req.strip()
    
    # Extract project title
    title_match = re.search(r"build (?:a|an)?\s+([^,\.]+?)(?:\s+with|\s+application|\s+system|\s+platform|$)", clean_text, re.IGNORECASE)
    if title_match:
        raw_name = title_match.group(1).strip()
        project_name = f"{raw_name.title()} Platform"
    else:
        project_name = "Custom Software Engineering System"
        
    project_slug = re.sub(r'[^a-zA-Z0-9]+', '-', project_name.lower()).strip('-')
    
    # Extract features / modules from "with ... and ..." clauses
    items = []
    with_match = re.search(r"with\s+(.+)$", clean_text, re.IGNORECASE)
    if with_match:
        clause = with_match.group(1)
        # Split on commas and 'and'
        parts = re.split(r",\s*|\s+and\s+", clause)
        for p in parts:
            p_clean = p.strip().strip('.').strip()
            if p_clean and len(p_clean) > 2:
                items.append(p_clean.title())
    
    if not items:
        items = ["Core Management", "User Operations", "Data Processing", "Reporting & Analytics"]
        
    return project_name, project_slug, items


async def ingest_and_normalize_node(state: PlannerState) -> Dict[str, Any]:
    """Node 1: Ingests user requirement, initializes tracking IDs and multi-agent context."""
    task_id = state.get("task_id") or str(uuid.uuid4())
    session_id = state.get("session_id") or f"session_{task_id}"
    user_id = state.get("user_id", "user_default_01")
    project_id = state.get("project_id", "proj_default_01")
    raw_req = state.get("original_requirement") or state.get("raw_requirement", "").strip()
    
    # Debug print as instructed
    print("\n========== PLANNER DEBUG ==========")
    print("RAW REQUIREMENT:")
    print(raw_req)
    print("===================================\n")
    
    logger.info(f"Ingesting requirement for Task ID: {task_id}", extra={"task_id": task_id, "node_name": "ingest_and_normalize"})
    
    return {
        "user_id": user_id,
        "project_id": project_id,
        "session_id": session_id,
        "current_agent": "PLANNER_AGENT",
        "current_step": "receive_requirement",
        "original_requirement": raw_req,
        "retry_count": state.get("retry_count", 0),
        "execution_status": "INITIALIZED",
        "errors": []
    }


async def ambiguity_analyzer_node(state: PlannerState) -> Dict[str, Any]:
    """Node 2: Analyzes ambiguities, formulates assumptions and architectural defaults."""
    raw_req = state.get("original_requirement", "")
    project_name, _, items = _extract_domain_and_features_from_text(raw_req)
    
    try:
        user_prompt = f"<user_requirement_data>\n{raw_req}\n</user_requirement_data>"
        result = await llm_client.generate_structured(
            prompt=user_prompt,
            system_prompt=AMBIGUITY_SYSTEM_PROMPT,
            schema=AmbiguityLLMResult
        )
        return {
            "current_step": "analyze_requirement",
            "clarifications": result.clarifications,
            "assumptions": result.assumptions,
            "is_blocked_on_clarification": result.is_blocked_on_clarification,
            "execution_status": "ANALYSIS_COMPLETE"
        }
    except Exception as ex:
        logger.warning(f"Ollama structured ambiguity call skipped, using dynamic heuristic parser: {ex}")
        
        clarifications = [
            ClarificationItem(
                ambiguity_id="AMB-01",
                question=f"Which database and storage engine is preferred for {project_name}?",
                severity="NON_BLOCKING",
                assumed_default="PostgreSQL 16 Relational Database with SQLAlchemy 2.0 & Alembic"
            ),
            ClarificationItem(
                ambiguity_id="AMB-02",
                question="What authentication and session management protocol is preferred?",
                severity="NON_BLOCKING",
                assumed_default="Stateless JWT (HMAC-SHA256) with Redis Session Caching"
            )
        ]
        
        assumptions = [
            AssumptionItem(id="ASM-01", category="TECHNICAL", assumption_text="System will use PostgreSQL for ACID-compliant persistence.", rationale=f"Guarantees transactional integrity across {items[0] if items else 'domain'} workflows."),
            AssumptionItem(id="ASM-02", category="SECURITY", assumption_text="Role-based access control (RBAC) and bcrypt password hashing applied to all user accounts.", rationale="Standard secure access practice."),
            AssumptionItem(id="ASM-03", category="INFRASTRUCTURE", assumption_text="Redis is utilized for session management, caching, and rate limiting.", rationale="Maintains low latency under peak concurrent access.")
        ]
        
        return {
            "current_step": "analyze_requirement",
            "clarifications": clarifications,
            "assumptions": assumptions,
            "is_blocked_on_clarification": False,
            "execution_status": "ANALYSIS_COMPLETE"
        }


async def requirement_decomposer_node(state: PlannerState) -> Dict[str, Any]:
    """Node 3: Decomposes requirements into structured FRs and NFRs dynamically based on input."""
    raw_req = state.get("original_requirement", "")
    project_name, _, items = _extract_domain_and_features_from_text(raw_req)
    
    try:
        user_prompt = f"<user_requirement_data>\n{raw_req}\n</user_requirement_data>"
        result = await llm_client.generate_structured(
            prompt=user_prompt,
            system_prompt=DECOMPOSITION_SYSTEM_PROMPT,
            schema=DecomposeLLMResult
        )
        return {
            "current_step": "extract_features",
            "functional_requirements": result.functional_requirements,
            "non_functional_requirements": result.non_functional_requirements,
            "execution_status": "FEATURES_EXTRACTED"
        }
    except Exception as ex:
        logger.warning(f"Ollama structured decomposer call skipped, using dynamic heuristic parser: {ex}")
        
        frs = []
        for idx, item in enumerate(items, start=1):
            mod_code = re.sub(r'[^a-zA-Z]', '', item).upper()[:4]
            frs.append(
                FunctionalReq(
                    id=f"FR-{mod_code}-{idx:02d}",
                    module=item.replace(" ", ""),
                    title=f"{item} Management & Operations",
                    user_story=f"As a user/administrator, I want to manage {item.lower()} so that operations are tracked securely and accurately.",
                    business_rules=[
                        f"All {item.lower()} data mutations must be validated against business schemas",
                        f"Audit timestamps and user ID references recorded on every {item.lower()} record"
                    ]
                )
            )
            
        nfrs = [
            NonFunctionalReq(id="NFR-SEC-01", category="SECURITY", constraint="All API communications encrypted via TLS 1.3 with RBAC role authorization.", target_metric="Zero unauthorized access & A+ SSL"),
            NonFunctionalReq(id="NFR-PERF-01", category="PERFORMANCE", constraint=f"API endpoints for {project_name} must maintain low latency under load.", target_metric="p95 latency < 150ms at 1000 RPS"),
            NonFunctionalReq(id="NFR-REL-01", category="RELIABILITY", constraint="All state transactions must maintain ACID atomicity with automated rollback.", target_metric="99.99% data consistency rate")
        ]
        
        return {
            "current_step": "extract_features",
            "functional_requirements": frs,
            "non_functional_requirements": nfrs,
            "execution_status": "FEATURES_EXTRACTED"
        }


async def module_and_architecture_node(state: PlannerState) -> Dict[str, Any]:
    """Node 4: Synthesizes recommended architecture, tech stack, and feature bounded contexts."""
    raw_req = state.get("original_requirement", "")
    project_name, project_slug, items = _extract_domain_and_features_from_text(raw_req)
    
    try:
        user_prompt = f"<user_requirement_data>\n{raw_req}\n</user_requirement_data>"
        result = await llm_client.generate_structured(
            prompt=user_prompt,
            system_prompt=MODULE_ARCHITECTURE_SYSTEM_PROMPT,
            schema=ArchitectureLLMResult
        )
        return {
            "current_step": "design_architecture",
            "recommended_tech_stack": result.recommended_tech_stack,
            "architecture_recommendation": result.architecture_recommendation,
            "features": result.features,
            "execution_status": "ARCHITECTURE_RECOMMENDED"
        }
    except Exception as ex:
        logger.warning(f"Ollama structured architecture call skipped, using dynamic heuristic parser: {ex}")
        
        tech_stack = RecommendedTechStack()
        bounded_ctx = [item.replace(" ", "") for item in items]
        
        arch = ArchitectureRecommendation(
            pattern="Modular Monolith with Clean Architecture & Domain-Driven Design",
            bounded_contexts=bounded_ctx
        )
        
        features = []
        for idx, item in enumerate(items, start=1):
            mod_code = re.sub(r'[^a-zA-Z]', '', item).upper()[:4]
            slug = item.lower().replace(" ", "_")
            features.append(
                FeatureSpec(
                    feature_id=f"FEAT-{mod_code}-{idx:02d}",
                    name=item,
                    purpose=f"Handles core business logic and API lifecycle for {item.lower()}.",
                    database_tables=[f"{slug}_records", f"{slug}_audit_logs"],
                    api_endpoints=[f"GET /{slug}", f"POST /{slug}", f"GET /{slug}/{{id}}"],
                    dependent_features=[f"FEAT-{re.sub(r'[^a-zA-Z]', '', items[0]).upper()[:4]}-01"] if idx > 1 else []
                )
            )
            
        return {
            "current_step": "design_architecture",
            "recommended_tech_stack": tech_stack,
            "architecture_recommendation": arch,
            "features": features,
            "execution_status": "ARCHITECTURE_RECOMMENDED"
        }


async def task_breakdown_and_dag_node(state: PlannerState) -> Dict[str, Any]:
    """Node 5: Builds atomic tasks with DAG dependencies and concrete file targets dynamically."""
    raw_req = state.get("original_requirement", "")
    project_name, project_slug, items = _extract_domain_and_features_from_text(raw_req)
    features = state.get("features", [])
    
    try:
        user_prompt = f"<user_requirement_data>\n{raw_req}\n</user_requirement_data>"
        result = await llm_client.generate_structured(
            prompt=user_prompt,
            system_prompt=TASK_DAG_SYSTEM_PROMPT,
            schema=TaskDagLLMResult
        )
        tasks = result.tasks
    except Exception as ex:
        logger.warning(f"Ollama structured task DAG call skipped, using dynamic heuristic parser: {ex}")
        
        tasks: List[AtomicTask] = []
        
        # 1. Foundation Database Task (Root)
        root_models = [f"app/models/{item.lower().replace(' ', '_')}.py" for item in items[:3]]
        tasks.append(
            AtomicTask(
                task_id="TASK-001",
                title=f"Create PostgreSQL Data Models & Alembic Migrations for {project_name}",
                feature_id=features[0].feature_id if features else "FEAT-CORE-01",
                task_type="SCHEMA",
                priority="CRITICAL",
                complexity="M",
                estimated_hours=2.5,
                upstream_dependencies=[],
                target_files=TargetFiles(create=root_models, modify=["app/models/__init__.py"]),
                acceptance_criteria=[
                    f"All {project_name} database entities defined with UUID primary keys and timestamps",
                    "Alembic autogenerate produces valid DDL without circular foreign key constraints"
                ]
            )
        )
        
        # 2. Service & Endpoint Tasks for each feature
        prev_task_id = "TASK-001"
        for idx, item in enumerate(items, start=2):
            task_num = f"TASK-{len(tasks)+1:03d}"
            slug = item.lower().replace(" ", "_")
            feat_id = features[idx-2].feature_id if idx-2 < len(features) else f"FEAT-{slug[:4].upper()}-01"
            
            tasks.append(
                AtomicTask(
                    task_id=task_num,
                    title=f"Implement {item} Service & REST API Endpoints",
                    feature_id=feat_id,
                    task_type="SERVICE",
                    priority="HIGH",
                    complexity="M",
                    estimated_hours=3.0,
                    upstream_dependencies=[prev_task_id],
                    target_files=TargetFiles(
                        create=[f"app/services/{slug}_service.py", f"app/api/v1/{slug}.py"],
                        modify=["app/main.py"]
                    ),
                    acceptance_criteria=[
                        f"CRUD service and business logic for {item} pass all schema validation checks",
                        f"REST endpoints for {item} return structured responses with standard HTTP status codes"
                    ]
                )
            )
            prev_task_id = task_num
            
        # 3. Final Integration & End-to-End Test Suite Task
        test_task_id = f"TASK-{len(tasks)+1:03d}"
        tasks.append(
            AtomicTask(
                task_id=test_task_id,
                title=f"Implement End-to-End Test Suite for {project_name}",
                feature_id=features[0].feature_id if features else "FEAT-CORE-01",
                task_type="TEST",
                priority="HIGH",
                complexity="M",
                estimated_hours=2.5,
                upstream_dependencies=[prev_task_id],
                target_files=TargetFiles(create=[f"tests/test_e2e_{project_slug}.py"], modify=["tests/conftest.py"]),
                acceptance_criteria=[
                    f"Pytest suite exercises full lifecycle for {', '.join(items[:3])}",
                    "Test suite reaches >= 80% line coverage with zero regression failures"
                ]
            )
        )

    deps_map = {t.task_id: t.upstream_dependencies for t in tasks}
    prio_map = {t.task_id: t.priority for t in tasks}
    ac_map = {t.task_id: t.acceptance_criteria for t in tasks}
    
    return {
        "current_step": "generate_tasks",
        "tasks": tasks,
        "dependencies": deps_map,
        "priorities": prio_map,
        "acceptance_criteria": ac_map,
        "execution_status": "TASKS_GENERATED"
    }


async def risk_and_estimation_node(state: PlannerState) -> Dict[str, Any]:
    """Node 6: Assesses technical, security, and integration risks with mitigations dynamically."""
    raw_req = state.get("original_requirement", "")
    project_name, _, items = _extract_domain_and_features_from_text(raw_req)
    
    try:
        user_prompt = f"<user_requirement_data>\n{raw_req}\n</user_requirement_data>"
        result = await llm_client.generate_structured(
            prompt=user_prompt,
            system_prompt=RISK_SYSTEM_PROMPT,
            schema=RiskLLMResult
        )
        return {
            "current_step": "risk_assessment",
            "risks": result.risks,
            "testing_strategy": result.testing_strategy,
            "deployment_recommendation": result.deployment_recommendation,
            "execution_status": "RISKS_ASSESSED"
        }
    except Exception as ex:
        logger.warning(f"Ollama structured risk call skipped, using dynamic heuristic parser: {ex}")
        
        risks = [
            RiskItem(
                risk_id="RISK-01",
                category="SECURITY",
                severity="HIGH",
                likelihood="MEDIUM",
                description=f"Unauthorized access or privilege escalation across {project_name} roles.",
                mitigation_strategy="Enforce granular RBAC middleware dependencies on all state-mutating endpoints."
            ),
            RiskItem(
                risk_id="RISK-02",
                category="TECHNICAL",
                severity="HIGH",
                likelihood="MEDIUM",
                description=f"Concurrency race conditions during simultaneous {items[1] if len(items)>1 else 'booking'} updates.",
                mitigation_strategy="Utilize PostgreSQL row-level locks (SELECT FOR UPDATE) inside atomic transactions."
            ),
            RiskItem(
                risk_id="RISK-03",
                category="INTEGRATION",
                severity="MEDIUM",
                likelihood="LOW",
                description="Network timeouts or third-party service latency affecting overall API responsiveness.",
                mitigation_strategy="Implement circuit breakers, connection pools, and Redis caching for read-heavy routes."
            )
        ]
        
        return {
            "current_step": "risk_assessment",
            "risks": risks,
            "testing_strategy": TestingStrategy(),
            "deployment_recommendation": DeploymentRecommendation(),
            "execution_status": "RISKS_ASSESSED"
        }


async def plan_synthesizer_node(state: PlannerState) -> Dict[str, Any]:
    """Node 7: Synthesizes the complete 14-component Master Software Development Plan dynamically."""
    raw_req = state.get("original_requirement", "")
    project_name, project_slug, items = _extract_domain_and_features_from_text(raw_req)
    tasks = state.get("tasks", [])
    
    _, _, topo_order = validator.validate_task_dag(tasks)
    critical_path = validator.calculate_critical_path(tasks, topo_order)
    
    # Dynamically divide tasks into logical phases
    phases: List[PlanPhase] = []
    chunk_size = max(1, len(tasks) // 3)
    phases.append(
        PlanPhase(
            phase_number=1,
            phase_name=f"Foundations & {items[0] if items else 'Core'}",
            description=f"Database models and core services for {project_name}.",
            task_ids=[t.task_id for t in tasks[:chunk_size+1]]
        )
    )
    if len(tasks) > chunk_size + 1:
        phases.append(
            PlanPhase(
                phase_number=2,
                phase_name=f"{items[1] if len(items)>1 else 'Operations'} & Business Services",
                description=f"Feature implementations and business workflows.",
                task_ids=[t.task_id for t in tasks[chunk_size+1:-1]]
            )
        )
    phases.append(
        PlanPhase(
            phase_number=len(phases)+1,
            phase_name="Testing & System Verification",
            description="End-to-end testing, security validation, and deployment preparation.",
            task_ids=[tasks[-1].task_id] if tasks else []
        )
    )
    
    total_hours = sum(t.estimated_hours for t in tasks)
    
    metadata = ExecutionMetadata(
        total_estimated_hours=total_hours,
        critical_path=critical_path,
        total_phases=len(phases),
        phases=phases
    )
    
    proj_info = ProjectInformation(
        project_name=project_name,
        project_slug=project_slug,
        version="1.0.0",
        summary=f"Enterprise-grade, modular {project_name} with clean architecture, robust data models, and automated test coverage.",
        domain=f"{project_name.split()[0]} Operations",
        target_environment="production"
    )
    
    req_container = RequirementsContainer(
        functional=state.get("functional_requirements", []),
        non_functional=state.get("non_functional_requirements", [])
    )
    
    plan = StructuredSoftwareDevelopmentPlan(
        project_information=proj_info,
        recommended_technology_stack=state.get("recommended_tech_stack", RecommendedTechStack()),
        architecture_recommendation=state.get("architecture_recommendation", ArchitectureRecommendation()),
        requirements=req_container,
        assumptions=state.get("assumptions", []),
        features=state.get("features", []),
        tasks=tasks,
        risks=state.get("risks", []),
        testing_strategy=state.get("testing_strategy", TestingStrategy()),
        deployment_recommendation=state.get("deployment_recommendation", DeploymentRecommendation()),
        execution_metadata=metadata
    )
    
    # Human approval state starts in PENDING
    approval = HumanApprovalState(
        status="PENDING",
        approved_by="Awaiting_Human_Review",
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    
    return {
        "current_step": "synthesize_plan",
        "critical_path": critical_path,
        "final_plan": plan,
        "human_approval": approval,
        "execution_status": "PLAN_SYNTHESIZED"
    }


async def plan_validator_node(state: PlannerState) -> Dict[str, Any]:
    """Node 8: Deterministically validates schema compliance and DAG acyclicity."""
    tasks = state.get("tasks", [])
    frs = state.get("functional_requirements", [])
    
    is_acyclic, errors, _ = validator.validate_task_dag(tasks)
    coverage_warnings = validator.audit_coverage(tasks, frs)
    all_errors = errors + coverage_warnings
    
    is_valid = is_acyclic and len(errors) == 0
    
    if is_valid and len(all_errors) == 0:
        status = "COMPLETED"
    elif is_valid:
        status = "COMPLETED_WITH_WARNINGS"
    else:
        status = "VALIDATION_FAILED"
        
    logger.info(f"Plan validation finished. Valid: {is_valid}. Errors/Warnings: {len(all_errors)}")
    
    return {
        "current_step": "validate_plan",
        "is_dag_acyclic": is_acyclic,
        "errors": all_errors,
        "execution_status": status
    }


async def plan_refinement_node(state: PlannerState) -> Dict[str, Any]:
    """Node 9: Refinement node for self-healing error recovery."""
    new_retries = state.get("retry_count", 0) + 1
    return {
        "current_step": "refine_plan",
        "retry_count": new_retries,
        "execution_status": "REFINING"
    }

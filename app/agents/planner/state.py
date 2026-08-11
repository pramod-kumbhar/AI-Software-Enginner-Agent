from typing import List, Dict, Optional, Any, Annotated
import operator
from typing_extensions import TypedDict
from app.schemas.plan import (
    ProjectInformation,
    RecommendedTechStack,
    ArchitectureRecommendation,
    FunctionalReq,
    NonFunctionalReq,
    AssumptionItem,
    ClarificationItem,
    FeatureSpec,
    AtomicTask,
    RiskItem,
    TestingStrategy,
    DeploymentRecommendation,
    StructuredSoftwareDevelopmentPlan,
    HumanApprovalState
)

class PlannerState(TypedDict, total=False):
    # Domain A: Multi-Agent Routing & Session Context (Fields 1-3, 14-16)
    user_id: str
    project_id: str
    session_id: str
    current_agent: str
    current_step: str
    execution_status: str
    
    # Domain B: Ingestion & Clarification Context (Fields 4-5)
    original_requirement: str
    target_tech_stack: Optional[Dict[str, str]]
    project_type: str
    max_tasks: int
    clarifications: List[ClarificationItem]
    assumptions: List[AssumptionItem]
    is_blocked_on_clarification: bool
    
    # Domain C: Specifications & Features (Fields 6-8)
    functional_requirements: List[FunctionalReq]
    non_functional_requirements: List[NonFunctionalReq]
    features: List[FeatureSpec]
    architecture_recommendation: ArchitectureRecommendation
    recommended_tech_stack: RecommendedTechStack
    
    # Domain D: Work Breakdown Structure (WBS) & Task DAG (Fields 9-12)
    tasks: List[AtomicTask]
    dependencies: Dict[str, List[str]]
    priorities: Dict[str, str]
    acceptance_criteria: Dict[str, List[str]]
    critical_path: List[str]
    is_dag_acyclic: bool
    
    # Domain E: Quality, Risks & Fault Tolerance (Fields 13, 17-18)
    risks: List[RiskItem]
    testing_strategy: TestingStrategy
    deployment_recommendation: DeploymentRecommendation
    errors: Annotated[List[str], operator.add]
    retry_count: int
    
    # Domain F: Human Gate & Final Deliverable (Fields 19-20)
    human_approval: HumanApprovalState
    final_plan: Optional[StructuredSoftwareDevelopmentPlan]

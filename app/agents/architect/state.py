from typing import TypedDict, List, Dict, Optional, Any, Annotated
import operator
from app.schemas.plan import (
    StructuredSoftwareDevelopmentPlan,
    ProjectInformation,
    FunctionalReq,
    NonFunctionalReq,
    FeatureSpec,
    AtomicTask,
    RecommendedTechStack,
    AssumptionItem,
    ClarificationItem
)
from app.schemas.architecture import (
    ArchitecturePatternEnum,
    ArchitectureComponent,
    ComponentRelationship,
    DatabaseDesign,
    APIDesign,
    SecurityDesign,
    AuthenticationDesign,
    AuthorizationDesign,
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

class ArchitectState(TypedDict, total=False):
    # Identifiers & Routing
    user_id: str
    project_id: str
    planner_task_id: str
    architect_task_id: str
    session_id: str
    current_agent: str
    current_step: str
    architecture_status: str
    
    # Ingested Planner Output
    planner_output: Optional[StructuredSoftwareDevelopmentPlan]
    project_information: Optional[ProjectInformation]
    functional_requirements: List[FunctionalReq]
    non_functional_requirements: List[NonFunctionalReq]
    features: List[FeatureSpec]
    tasks: List[AtomicTask]
    dependencies: Dict[str, List[str]]
    technology_stack: Optional[RecommendedTechStack]
    
    # Architectural Deliverables
    architecture_pattern: ArchitecturePatternEnum
    architecture_overview: str
    components: List[ArchitectureComponent]
    component_relationships: List[ComponentRelationship]
    data_flow: str
    database_design: Optional[DatabaseDesign]
    api_design: Optional[APIDesign]
    authentication_design: Optional[AuthenticationDesign]
    authorization_design: Optional[AuthorizationDesign]
    security_design: Optional[SecurityDesign]
    caching_strategy: Optional[CachingStrategy]
    background_processing: Optional[BackgroundProcessing]
    testing_design: Optional[TestStrategy]
    deployment_design: Optional[DeploymentStrategy]
    folder_structure: Optional[FolderStructureBlueprint]
    hld: Optional[HighLevelDesign]
    lld: Optional[LowLevelDesign]
    architecture_decisions: List[ArchitectureDecision]
    risks: List[ArchitectureRisk]
    tradeoffs: List[ArchitectureTradeoff]
    assumptions: List[AssumptionItem]
    clarifications: List[ClarificationItem]
    
    # Quality, Validation & Governance
    validation_results: Optional[ValidationResult]
    human_approval: Optional[HumanApproval]
    final_architecture: Optional[StructuredSoftwareArchitecture]
    
    # Fault Tolerance & Retries
    errors: Annotated[List[str], operator.add]
    retry_count: int
    execution_metadata: Dict[str, Any]

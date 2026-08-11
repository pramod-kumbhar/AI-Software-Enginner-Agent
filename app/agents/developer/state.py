from typing import TypedDict, List, Dict, Optional, Any, Annotated
import operator
from app.schemas.architecture import StructuredSoftwareArchitecture, HumanApproval
from app.schemas.developer import (
    ImplementationPlan,
    GeneratedFile,
    StaticValidationResult,
    TestExecutionResult,
    FailureAnalysis,
    RepairAttempt,
    ArchitectureDeviation,
    ImplementationReport
)

class DeveloperState(TypedDict, total=False):
    # Identifiers & Routing
    user_id: str
    project_id: str
    architect_task_id: str
    developer_task_id: str
    session_id: str
    current_agent: str
    current_step: str
    implementation_status: str
    workspace_directory: str
    
    # Ingested Architecture
    approved_architecture: Optional[StructuredSoftwareArchitecture]
    
    # Planning & Structure
    implementation_plan: Optional[ImplementationPlan]
    project_structure: List[str]
    dependencies: List[str]
    files_to_create: List[str]
    files_to_modify: List[str]
    files_to_delete: List[str]
    
    # Generated Code & Tests
    generated_files: List[GeneratedFile]
    modified_files: List[str]
    code_generation_results: Dict[str, Any]
    
    # Validation & Quality
    validation_results: Optional[StaticValidationResult]
    deviations: List[ArchitectureDeviation]
    
    # Test Execution & Self-Healing Repair
    test_results: Optional[TestExecutionResult]
    test_failures: List[str]
    failure_analysis: Optional[FailureAnalysis]
    repair_attempts: int
    repair_history: List[RepairAttempt]
    
    # Human Review & Final Report
    human_approval: Optional[HumanApproval]
    implementation_report: Optional[ImplementationReport]
    
    # Fault Tolerance & Retries
    errors: Annotated[List[str], operator.add]
    retry_count: int
    execution_metadata: Dict[str, Any]

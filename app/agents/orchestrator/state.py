from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict
from datetime import datetime, timezone

class AgentState(TypedDict, total=False):
    """
    Strongly-Typed Persistent Agent State for LangGraph Durable Execution.
    Tracks end-to-end multi-agent outputs, human approvals, rework iterations, and checkpoints.
    """
    execution_id: str
    thread_id: str
    user_id: str
    project_id: str
    task_id: str
    
    current_phase: str
    current_node: str
    status: str # AgentExecutionStatusEnum value
    
    requirements: Dict[str, Any]
    plan: Dict[str, Any]
    architecture: Dict[str, Any]
    implementation_plan: Dict[str, Any]
    
    generated_files: List[str]
    changed_files: List[str]
    test_results: Dict[str, Any]
    security_results: Dict[str, Any]
    release_plan: Dict[str, Any]
    deployment_plan: Dict[str, Any]
    
    approval_required: bool
    approval_id: Optional[str]
    approval_status: Optional[str]
    approval_type: Optional[str]
    human_feedback: Optional[str]
    rejection_reason: Optional[str]
    
    retry_count: int
    repair_count: int
    rework_count: int
    
    token_usage: int
    estimated_cost: float
    risk_score: float
    risk_level: str # RiskLevelEnum value
    
    errors: List[str]
    warnings: List[str]
    action_hash: Optional[str]
    
    created_at: str
    updated_at: str

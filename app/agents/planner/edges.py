from typing import Literal
from app.agents.planner.state import PlannerState
from app.core.config import settings

def check_ambiguity_severity(state: PlannerState) -> Literal["proceed", "blocked_on_clarification"]:
    """
    Evaluates whether ambiguities block graph execution.
    If blocking, pauses for user clarification. Otherwise proceeds with defaults.
    """
    if state.get("is_blocked_on_input", False):
        return "blocked_on_clarification"
    return "proceed"

def validate_plan_completeness(state: PlannerState) -> Literal["valid", "retry_refinement", "fatal_failure"]:
    """
    Evaluates validation output:
    - If valid and acyclic: transitions to END.
    - If errors exist and retries remain: transitions to refinement loop.
    - If retries exceeded: stops in fatal error state.
    """
    is_acyclic = state.get("is_dag_acyclic", False)
    errors = state.get("validation_errors", [])
    iteration = state.get("iteration_count", 0)
    
    if is_acyclic and len(errors) == 0:
        return "valid"
    
    if iteration < settings.MAX_PLANNING_RETRIES:
        return "retry_refinement"
        
    return "fatal_failure"

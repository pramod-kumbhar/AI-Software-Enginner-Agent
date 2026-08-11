from typing import Literal
from app.agents.architect.state import ArchitectState

def check_planner_validity(state: ArchitectState) -> Literal["proceed", "missing_plan"]:
    if not state.get("planner_output"):
        return "missing_plan"
    return "proceed"

def check_architecture_validation(state: ArchitectState) -> Literal["proceed", "refine"]:
    val_res = state.get("validation_results")
    if val_res and val_res.validation_status == "FAILED" and state.get("retry_count", 0) < 3:
        return "refine"
    return "proceed"

from typing import Literal
from app.agents.developer.state import DeveloperState

def check_architecture_validity(state: DeveloperState) -> Literal["proceed", "missing_arch"]:
    if not state.get("approved_architecture"):
        return "missing_arch"
    return "proceed"

def check_test_execution_outcome(state: DeveloperState) -> Literal["tests_pass", "tests_fail", "repair_limit_reached"]:
    test_res = state.get("test_results")
    if test_res and test_res.all_passed:
        return "tests_pass"
        
    repair_count = state.get("repair_attempts", 0)
    if repair_count >= 3:
        return "repair_limit_reached"
        
    return "tests_fail"

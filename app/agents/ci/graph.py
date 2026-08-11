from langgraph.graph import StateGraph, END
from app.agents.ci.state import CIMonitorState
from app.schemas.ci import CIRunStatusEnum
from app.agents.ci.nodes import (
    monitor_ci_run_node,
    get_failed_jobs_node,
    get_failure_logs_node,
    classify_failure_node,
    root_cause_analysis_node,
    repairability_check_node,
    repair_planning_node,
    approval_policy_check_node,
    developer_repair_node,
    local_verification_node,
    qa_verification_node,
    update_branch_and_ci_retry_node
)

def should_repair_after_ci_check(state: CIMonitorState) -> str:
    status = state.get("status")
    if status == CIRunStatusEnum.CI_PASSED:
        return "end_passed"
    return "get_failed_jobs"

def route_repairability(state: CIMonitorState) -> str:
    status = state.get("status")
    if status == CIRunStatusEnum.BLOCKED:
        return "end_blocked"
    return "repair_planning"

def route_approval(state: CIMonitorState) -> str:
    status = state.get("status")
    if status == CIRunStatusEnum.APPROVAL_PENDING:
        return "end_approval_pending"
    return "developer_repair"

def route_retry(state: CIMonitorState) -> str:
    status = state.get("status")
    attempt = state.get("attempt_count", 1)
    max_attempts = state.get("max_attempts", 3)
    
    if status in (CIRunStatusEnum.READY_FOR_REVIEW, CIRunStatusEnum.CI_PASSED):
        return "end_success"
    elif status == CIRunStatusEnum.BLOCKED or attempt > max_attempts:
        return "end_blocked"
    return "monitor_ci_run"

# Build StateGraph
workflow = StateGraph(CIMonitorState)

# 1. Add Nodes
workflow.add_node("monitor_ci_run", monitor_ci_run_node)
workflow.add_node("get_failed_jobs", get_failed_jobs_node)
workflow.add_node("get_failure_logs", get_failure_logs_node)
workflow.add_node("classify_failure", classify_failure_node)
workflow.add_node("root_cause_analysis", root_cause_analysis_node)
workflow.add_node("repairability_check", repairability_check_node)
workflow.add_node("repair_planning", repair_planning_node)
workflow.add_node("approval_policy_check", approval_policy_check_node)
workflow.add_node("developer_repair", developer_repair_node)
workflow.add_node("local_verification", local_verification_node)
workflow.add_node("qa_verification", qa_verification_node)
workflow.add_node("update_branch_and_ci_retry", update_branch_and_ci_retry_node)

# 2. Set Entry Point
workflow.set_entry_point("monitor_ci_run")

# 3. Add Edges & Conditional Routing
workflow.add_conditional_edges(
    "monitor_ci_run",
    should_repair_after_ci_check,
    {
        "end_passed": END,
        "get_failed_jobs": "get_failed_jobs"
    }
)

workflow.add_edge("get_failed_jobs", "get_failure_logs")
workflow.add_edge("get_failure_logs", "classify_failure")
workflow.add_edge("classify_failure", "root_cause_analysis")
workflow.add_edge("root_cause_analysis", "repairability_check")

workflow.add_conditional_edges(
    "repairability_check",
    route_repairability,
    {
        "end_blocked": END,
        "repair_planning": "repair_planning"
    }
)

workflow.add_edge("repair_planning", "approval_policy_check")

workflow.add_conditional_edges(
    "approval_policy_check",
    route_approval,
    {
        "end_approval_pending": END,
        "developer_repair": "developer_repair"
    }
)

workflow.add_edge("developer_repair", "local_verification")
workflow.add_edge("local_verification", "qa_verification")
workflow.add_edge("qa_verification", "update_branch_and_ci_retry")

workflow.add_conditional_edges(
    "update_branch_and_ci_retry",
    route_retry,
    {
        "end_success": END,
        "end_blocked": END,
        "monitor_ci_run": "monitor_ci_run"
    }
)

# Compile Graph
ci_repair_agent = workflow.compile()

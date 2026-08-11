from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.security.state import SecurityState
from app.agents.security.nodes import (
    load_context_node,
    threat_model_node,
    prompt_injection_scan_node,
    secret_scan_node,
    code_security_scan_node,
    dependency_scan_node,
    tool_security_scan_node,
    authorization_scan_node,
    api_security_scan_node,
    ci_security_scan_node,
    deployment_security_scan_node,
    risk_calculation_node,
    policy_check_node,
    security_report_node,
    repair_node,
    rescan_node,
    finalize_node
)
from app.schemas.security import SecurityDecisionEnum

def route_after_policy(state: SecurityState) -> str:
    """Routes to repair if fixable vulnerabilities exist and attempts < 3, else finalizes."""
    findings = state.get("findings", [])
    has_auto_fixable = any(f.status == "OPEN" and f.auto_fixable for f in findings)
    attempts = state.get("repair_attempts", 0)
    max_attempts = state.get("max_repair_attempts", 3)

    if state.get("is_blocked") and has_auto_fixable and attempts < max_attempts:
        return "repair"
    return "finalize"

def route_after_rescan(state: SecurityState) -> str:
    """Routes to another repair attempt if issues remain and attempts < 3."""
    findings = state.get("findings", [])
    has_auto_fixable = any(f.status == "OPEN" and f.auto_fixable for f in findings)
    attempts = state.get("repair_attempts", 0)
    max_attempts = state.get("max_repair_attempts", 3)

    if state.get("is_blocked") and has_auto_fixable and attempts < max_attempts:
        return "repair"
    return "finalize"

def build_security_graph() -> StateGraph:
    builder = StateGraph(SecurityState)

    # Register all 17 nodes
    builder.add_node("load_context", load_context_node)
    builder.add_node("threat_model", threat_model_node)
    builder.add_node("prompt_injection_scan", prompt_injection_scan_node)
    builder.add_node("secret_scan", secret_scan_node)
    builder.add_node("code_security_scan", code_security_scan_node)
    builder.add_node("dependency_scan", dependency_scan_node)
    builder.add_node("tool_security_scan", tool_security_scan_node)
    builder.add_node("authorization_scan", authorization_scan_node)
    builder.add_node("api_security_scan", api_security_scan_node)
    builder.add_node("ci_security_scan", ci_security_scan_node)
    builder.add_node("deployment_security_scan", deployment_security_scan_node)
    builder.add_node("risk_calculation", risk_calculation_node)
    builder.add_node("policy_check", policy_check_node)
    builder.add_node("security_report", security_report_node)
    builder.add_node("repair", repair_node)
    builder.add_node("rescan", rescan_node)
    builder.add_node("finalize", finalize_node)

    # Linear scan pipeline
    builder.add_edge(START, "load_context")
    builder.add_edge("load_context", "threat_model")
    builder.add_edge("threat_model", "prompt_injection_scan")
    builder.add_edge("prompt_injection_scan", "secret_scan")
    builder.add_edge("secret_scan", "code_security_scan")
    builder.add_edge("code_security_scan", "dependency_scan")
    builder.add_edge("dependency_scan", "tool_security_scan")
    builder.add_edge("tool_security_scan", "authorization_scan")
    builder.add_edge("authorization_scan", "api_security_scan")
    builder.add_edge("api_security_scan", "ci_security_scan")
    builder.add_edge("ci_security_scan", "deployment_security_scan")
    builder.add_edge("deployment_security_scan", "risk_calculation")
    builder.add_edge("risk_calculation", "policy_check")
    builder.add_edge("policy_check", "security_report")

    # Conditional Branching for Auto-Repair Loop
    builder.add_conditional_edges(
        "security_report",
        route_after_policy,
        {
            "repair": "repair",
            "finalize": "finalize"
        }
    )

    builder.add_edge("repair", "rescan")

    builder.add_conditional_edges(
        "rescan",
        route_after_rescan,
        {
            "repair": "repair",
            "finalize": "finalize"
        }
    )

    builder.add_edge("finalize", END)

    checkpointer = MemorySaver()
    return builder.compile(checkpointer=checkpointer)

security_agent = build_security_graph()

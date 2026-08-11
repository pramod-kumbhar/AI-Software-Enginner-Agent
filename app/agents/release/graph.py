from langgraph.graph import StateGraph, START, END
from app.agents.release.state import ReleaseState
from app.schemas.release import ReleaseStatusEnum, EnvironmentEnum, ReleaseDecisionEnum
from app.agents.release.nodes import (
    load_release_context_node,
    validate_ci_node,
    validate_qa_node,
    validate_security_node,
    validate_architecture_node,
    validate_artifact_node,
    calculate_release_risk_node,
    generate_release_plan_node,
    policy_check_node,
    deploy_staging_node,
    validate_staging_node,
    deploy_production_node,
    health_check_node,
    observe_node,
    rollback_node,
    finalize_release_node
)

def route_after_policy(state: ReleaseState) -> str:
    if state.get("is_blocked"):
        return "finalize_release"
    return "deploy_staging"

def route_after_staging(state: ReleaseState) -> str:
    if state.get("is_blocked"):
        return "finalize_release"
    
    target_env = state.get("target_environment", EnvironmentEnum.STAGING)
    if isinstance(target_env, str):
        target_env = EnvironmentEnum(target_env)
    approval_granted = state.get("approval_granted", False)
    
    # Production deployment strictly requires explicit human approval
    if target_env == EnvironmentEnum.PRODUCTION and approval_granted:
        return "deploy_production"
    
    return "finalize_release"


def route_after_production_health(state: ReleaseState) -> str:
    if state.get("status") == ReleaseStatusEnum.ROLLBACK_PENDING:
        return "rollback"
    return "observe"

def build_release_graph() -> StateGraph:
    workflow = StateGraph(ReleaseState)

    # 1. Add Nodes
    workflow.add_node("load_release_context", load_release_context_node)
    workflow.add_node("validate_ci", validate_ci_node)
    workflow.add_node("validate_qa", validate_qa_node)
    workflow.add_node("validate_security", validate_security_node)
    workflow.add_node("validate_architecture", validate_architecture_node)
    workflow.add_node("validate_artifact", validate_artifact_node)
    workflow.add_node("calculate_release_risk", calculate_release_risk_node)
    workflow.add_node("generate_release_plan", generate_release_plan_node)
    workflow.add_node("policy_check", policy_check_node)
    workflow.add_node("deploy_staging", deploy_staging_node)
    workflow.add_node("validate_staging", validate_staging_node)
    workflow.add_node("deploy_production", deploy_production_node)
    workflow.add_node("health_check", health_check_node)
    workflow.add_node("observe", observe_node)
    workflow.add_node("rollback", rollback_node)
    workflow.add_node("finalize_release", finalize_release_node)

    # 2. Add Linear Edges
    workflow.add_edge(START, "load_release_context")
    workflow.add_edge("load_release_context", "validate_ci")
    workflow.add_edge("validate_ci", "validate_qa")
    workflow.add_edge("validate_qa", "validate_security")
    workflow.add_edge("validate_security", "validate_architecture")
    workflow.add_edge("validate_architecture", "validate_artifact")
    workflow.add_edge("validate_artifact", "calculate_release_risk")
    workflow.add_edge("calculate_release_risk", "generate_release_plan")
    workflow.add_edge("generate_release_plan", "policy_check")

    # 3. Conditional Routing
    workflow.add_conditional_edges(
        "policy_check",
        route_after_policy,
        {
            "deploy_staging": "deploy_staging",
            "finalize_release": "finalize_release"
        }
    )
    workflow.add_edge("deploy_staging", "validate_staging")
    workflow.add_conditional_edges(
        "validate_staging",
        route_after_staging,
        {
            "deploy_production": "deploy_production",
            "finalize_release": "finalize_release"
        }
    )
    workflow.add_edge("deploy_production", "health_check")
    workflow.add_conditional_edges(
        "health_check",
        route_after_production_health,
        {
            "observe": "observe",
            "rollback": "rollback"
        }
    )
    workflow.add_edge("observe", "finalize_release")
    workflow.add_edge("rollback", "finalize_release")
    workflow.add_edge("finalize_release", END)

    return workflow.compile()

release_agent = build_release_graph()

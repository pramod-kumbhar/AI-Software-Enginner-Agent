from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.architect.state import ArchitectState
from app.agents.architect.nodes import (
    validate_planner_output_node,
    analyze_requirements_node,
    select_architecture_node,
    design_components_node,
    design_database_node,
    design_api_node,
    design_security_node,
    design_testing_node,
    design_deployment_node,
    generate_hld_node,
    generate_lld_node,
    validate_architecture_node,
    human_review_node,
    persist_architecture_node
)
from app.agents.architect.edges import (
    check_planner_validity,
    check_architecture_validation
)

def create_architect_graph(checkpointer=None):
    """
    Constructs and compiles the 14-node Architect Agent LangGraph workflow.
    """
    workflow = StateGraph(ArchitectState)
    
    # 1. Register 14 Nodes
    workflow.add_node("validate_planner_output", validate_planner_output_node)
    workflow.add_node("analyze_requirements", analyze_requirements_node)
    workflow.add_node("select_architecture", select_architecture_node)
    workflow.add_node("design_components", design_components_node)
    workflow.add_node("design_database", design_database_node)
    workflow.add_node("design_api", design_api_node)
    workflow.add_node("design_security", design_security_node)
    workflow.add_node("design_testing", design_testing_node)
    workflow.add_node("design_deployment", design_deployment_node)
    workflow.add_node("generate_hld", generate_hld_node)
    workflow.add_node("generate_lld", generate_lld_node)
    workflow.add_node("validate_architecture", validate_architecture_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("persist_architecture", persist_architecture_node)
    
    # 2. Add Edges
    workflow.add_edge(START, "validate_planner_output")
    
    workflow.add_conditional_edges(
        "validate_planner_output",
        check_planner_validity,
        {
            "proceed": "analyze_requirements",
            "missing_plan": END
        }
    )
    
    workflow.add_edge("analyze_requirements", "select_architecture")
    workflow.add_edge("select_architecture", "design_components")
    workflow.add_edge("design_components", "design_database")
    workflow.add_edge("design_database", "design_api")
    workflow.add_edge("design_api", "design_security")
    workflow.add_edge("design_security", "design_testing")
    workflow.add_edge("design_testing", "design_deployment")
    workflow.add_edge("design_deployment", "generate_hld")
    workflow.add_edge("generate_hld", "generate_lld")
    workflow.add_edge("generate_lld", "validate_architecture")
    
    workflow.add_conditional_edges(
        "validate_architecture",
        check_architecture_validation,
        {
            "proceed": "human_review",
            "refine": "select_architecture"
        }
    )
    
    workflow.add_edge("human_review", "persist_architecture")
    workflow.add_edge("persist_architecture", END)
    
    return workflow.compile(checkpointer=checkpointer)

architect_agent = create_architect_graph()

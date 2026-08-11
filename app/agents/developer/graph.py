from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.developer.state import DeveloperState
from app.agents.developer.nodes import (
    validate_architecture_node,
    create_implementation_plan_node,
    determine_project_structure_node,
    determine_dependencies_node,
    generate_code_node,
    generate_tests_node,
    write_files_node,
    static_validation_node,
    run_tests_node,
    analyze_failures_node,
    repair_code_node,
    validate_implementation_node,
    prepare_human_review_node,
    persist_result_node
)
from app.agents.developer.edges import (
    check_architecture_validity,
    check_test_execution_outcome
)

def create_developer_graph(checkpointer=None):
    """
    Constructs and compiles the 14-node Developer Agent LangGraph workflow.
    """
    workflow = StateGraph(DeveloperState)
    
    # 1. Register 14 Nodes
    workflow.add_node("validate_architecture", validate_architecture_node)
    workflow.add_node("create_implementation_plan", create_implementation_plan_node)
    workflow.add_node("determine_project_structure", determine_project_structure_node)
    workflow.add_node("determine_dependencies", determine_dependencies_node)
    workflow.add_node("generate_code", generate_code_node)
    workflow.add_node("generate_tests", generate_tests_node)
    workflow.add_node("write_files", write_files_node)
    workflow.add_node("static_validation", static_validation_node)
    workflow.add_node("run_tests", run_tests_node)
    workflow.add_node("analyze_failures", analyze_failures_node)
    workflow.add_node("repair_code", repair_code_node)
    workflow.add_node("validate_implementation", validate_implementation_node)
    workflow.add_node("prepare_human_review", prepare_human_review_node)
    workflow.add_node("persist_result", persist_result_node)
    
    # 2. Add Edges
    workflow.add_edge(START, "validate_architecture")
    
    workflow.add_conditional_edges(
        "validate_architecture",
        check_architecture_validity,
        {
            "proceed": "create_implementation_plan",
            "missing_arch": END
        }
    )
    
    workflow.add_edge("create_implementation_plan", "determine_project_structure")
    workflow.add_edge("determine_project_structure", "determine_dependencies")
    workflow.add_edge("determine_dependencies", "generate_code")
    workflow.add_edge("generate_code", "generate_tests")
    workflow.add_edge("generate_tests", "write_files")
    workflow.add_edge("write_files", "static_validation")
    workflow.add_edge("static_validation", "run_tests")
    
    # 3. Test Result & Self-Healing Repair Loop
    workflow.add_conditional_edges(
        "run_tests",
        check_test_execution_outcome,
        {
            "tests_pass": "validate_implementation",
            "tests_fail": "analyze_failures",
            "repair_limit_reached": "validate_implementation"
        }
    )
    
    workflow.add_edge("analyze_failures", "repair_code")
    workflow.add_edge("repair_code", "write_files")
    
    workflow.add_edge("validate_implementation", "prepare_human_review")
    workflow.add_edge("prepare_human_review", "persist_result")
    workflow.add_edge("persist_result", END)
    
    return workflow.compile(checkpointer=checkpointer)

developer_agent = create_developer_graph()

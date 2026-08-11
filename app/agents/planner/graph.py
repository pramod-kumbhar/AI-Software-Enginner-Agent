from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.agents.planner.state import PlannerState
from app.agents.planner.nodes import (
    ingest_and_normalize_node,
    ambiguity_analyzer_node,
    requirement_decomposer_node,
    module_and_architecture_node,
    task_breakdown_and_dag_node,
    risk_and_estimation_node,
    plan_synthesizer_node,
    plan_validator_node,
    plan_refinement_node
)
from app.agents.planner.edges import (
    check_ambiguity_severity,
    validate_plan_completeness
)

def create_planner_graph(checkpointer=None):
    """
    Constructs and compiles the Planner Agent LangGraph workflow.
    """
    workflow = StateGraph(PlannerState)
    
    # 1. Register Nodes
    workflow.add_node("ingest_and_normalize", ingest_and_normalize_node)
    workflow.add_node("ambiguity_analyzer", ambiguity_analyzer_node)
    workflow.add_node("requirement_decomposer", requirement_decomposer_node)
    workflow.add_node("module_and_architecture", module_and_architecture_node)
    workflow.add_node("task_breakdown_and_dag", task_breakdown_and_dag_node)
    workflow.add_node("risk_and_estimation", risk_and_estimation_node)
    workflow.add_node("plan_synthesizer", plan_synthesizer_node)
    workflow.add_node("plan_validator", plan_validator_node)
    workflow.add_node("plan_refinement", plan_refinement_node)
    
    # 2. Add Deterministic Edges
    workflow.add_edge(START, "ingest_and_normalize")
    workflow.add_edge("ingest_and_normalize", "ambiguity_analyzer")
    
    # 3. Add Conditional Edge for Ambiguity Check
    workflow.add_conditional_edges(
        "ambiguity_analyzer",
        check_ambiguity_severity,
        {
            "proceed": "requirement_decomposer",
            "blocked_on_clarification": END
        }
    )
    
    workflow.add_edge("requirement_decomposer", "module_and_architecture")
    workflow.add_edge("module_and_architecture", "task_breakdown_and_dag")
    workflow.add_edge("task_breakdown_and_dag", "risk_and_estimation")
    workflow.add_edge("risk_and_estimation", "plan_synthesizer")
    workflow.add_edge("plan_synthesizer", "plan_validator")
    
    # 4. Add Conditional Edge for Plan Validation & Cycles
    workflow.add_conditional_edges(
        "plan_validator",
        validate_plan_completeness,
        {
            "valid": END,
            "retry_refinement": "plan_refinement",
            "fatal_failure": END
        }
    )
    
    # Refinement loops back to Task Breakdown
    workflow.add_edge("plan_refinement", "task_breakdown_and_dag")
    
    # Default in-memory checkpointer if none provided
    memory = checkpointer if checkpointer is not None else MemorySaver()
    
    return workflow.compile(checkpointer=memory)

# Pre-compiled default instance
planner_agent = create_planner_graph()

import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.orchestrator.state import AgentState
from app.agents.orchestrator.nodes import (
    planner_node,
    architect_node,
    human_architecture_approval_gate,
    architect_rework_node,
    developer_node,
    qa_node,
    security_node,
    release_node,
    human_deployment_approval_gate,
    deployment_node,
    complete_node
)
from app.services.approval_service import approval_service
from app.services.timeline_service import timeline_service
from app.services.storage import storage_service
from app.schemas.approval import (
    ApprovalStatusEnum,
    ApprovalDecisionEnum,
    AgentExecutionStatusEnum,
    ApprovalDecisionRequest,
    ReviewerRoleEnum
)
from app.core.logger import get_logger

logger = get_logger("orchestrator_graph")

# Conditional Routing Functions
def route_after_arch_gate(state: AgentState) -> str:
    status = state.get("status")
    appr_status = state.get("approval_status")

    if appr_status == ApprovalStatusEnum.APPROVED.value:
        return "developer"
    elif appr_status in [ApprovalStatusEnum.REJECTED.value, ApprovalStatusEnum.CHANGES_REQUESTED.value]:
        return "architect_rework"
    elif status == AgentExecutionStatusEnum.CANCELLED.value:
        return END
    elif status == AgentExecutionStatusEnum.WAITING_FOR_APPROVAL.value:
        # Pause execution and wait for human resolution
        return END
    return "developer"

def route_after_deploy_gate(state: AgentState) -> str:
    status = state.get("status")
    appr_status = state.get("approval_status")

    if appr_status == ApprovalStatusEnum.APPROVED.value:
        return "deployment"
    elif status in [AgentExecutionStatusEnum.CANCELLED.value, AgentExecutionStatusEnum.REJECTED.value]:
        return END
    elif status == AgentExecutionStatusEnum.WAITING_FOR_APPROVAL.value:
        # Pause execution and wait for human resolution
        return END
    return "deployment"


def build_orchestrator_graph() -> Any:
    """Construct the compiled LangGraph StateGraph with durable checkpointer."""
    workflow = StateGraph(AgentState)

    # 1. Register Nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("architect", architect_node)
    workflow.add_node("human_arch_gate", human_architecture_approval_gate)
    workflow.add_node("architect_rework", architect_rework_node)
    workflow.add_node("developer", developer_node)
    workflow.add_node("qa", qa_node)
    workflow.add_node("security", security_node)
    workflow.add_node("release", release_node)
    workflow.add_node("human_deploy_gate", human_deployment_approval_gate)
    workflow.add_node("deployment", deployment_node)
    workflow.add_node("complete", complete_node)

    # 2. Register Edges
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "architect")
    workflow.add_edge("architect", "human_arch_gate")

    workflow.add_conditional_edges(
        "human_arch_gate",
        route_after_arch_gate,
        {
            "developer": "developer",
            "architect_rework": "architect_rework",
            END: END
        }
    )

    workflow.add_edge("architect_rework", "architect")
    workflow.add_edge("developer", "qa")
    workflow.add_edge("qa", "security")
    workflow.add_edge("security", "release")
    workflow.add_edge("release", "human_deploy_gate")

    workflow.add_conditional_edges(
        "human_deploy_gate",
        route_after_deploy_gate,
        {
            "deployment": "deployment",
            END: END
        }
    )

    workflow.add_edge("deployment", "complete")
    workflow.add_edge("complete", END)

    checkpointer = MemorySaver()
    return workflow.compile(checkpointer=checkpointer)

orchestrator_graph = build_orchestrator_graph()


class MasterOrchestrator:
    """
    Day 15 Master Agent Orchestrator Engine.
    Coordinates execution start, approval resolution, thread resumption, pausing, and cancellation.
    """
    def __init__(self):
        self.graph = orchestrator_graph

    async def start_execution(
        self,
        prompt: str,
        project_id: str = "proj_default",
        user_id: str = "user_default",
        task_id: Optional[str] = None
    ) -> AgentState:
        execution_id = f"exec_{uuid.uuid4().hex[:10]}"
        thread_id = f"thread_{execution_id}"
        now_iso = datetime.now(timezone.utc).isoformat()

        initial_state: AgentState = {
            "execution_id": execution_id,
            "thread_id": thread_id,
            "user_id": user_id,
            "project_id": project_id,
            "task_id": task_id or execution_id,
            "current_phase": "INITIATED",
            "current_node": "planner",
            "status": AgentExecutionStatusEnum.RUNNING.value,
            "requirements": {"prompt": prompt},
            "plan": {},
            "architecture": {},
            "implementation_plan": {},
            "generated_files": [],
            "changed_files": [],
            "test_results": {},
            "security_results": {},
            "release_plan": {},
            "deployment_plan": {},
            "approval_required": False,
            "approval_id": None,
            "approval_status": None,
            "approval_type": None,
            "human_feedback": None,
            "rejection_reason": None,
            "retry_count": 0,
            "repair_count": 0,
            "rework_count": 0,
            "token_usage": 0,
            "estimated_cost": 0.0,
            "risk_score": 0.0,
            "risk_level": "LOW",
            "errors": [],
            "warnings": [],
            "action_hash": None,
            "created_at": now_iso,
            "updated_at": now_iso
        }

        config = {"configurable": {"thread_id": thread_id}}
        logger.info(f"STARTING ORCHESTRATED EXECUTION: [{execution_id}] (Thread: {thread_id})")
        
        # Invoke graph until first gate/interrupt
        result_state = await self.graph.ainvoke(initial_state, config=config)
        storage_service.save_agent_checkpoint(thread_id, result_state)
        storage_service.save_agent_execution(execution_id, result_state)
        return result_state

    async def resume_execution(
        self,
        execution_id: str,
        decision_req: Optional[ApprovalDecisionRequest] = None,
        feedback: Optional[str] = None
    ) -> AgentState:
        """
        Resume an interrupted execution thread after applying human decision.
        """
        exec_data = storage_service.get_agent_execution(execution_id)
        if not exec_data:
            raise ValueError(f"Execution '{execution_id}' not found.")

        thread_id = exec_data.get("thread_id", f"thread_{execution_id}")
        state: AgentState = dict(exec_data) # type: ignore
        config = {"configurable": {"thread_id": thread_id}}

        # If an approval decision is passed, resolve it first
        approval_id = state.get("approval_id")
        if approval_id and decision_req:
            resolved_req = approval_service.resolve_approval(approval_id, decision_req)
            state["approval_status"] = resolved_req.status.value
            state["human_feedback"] = decision_req.feedback or feedback
            
            if decision_req.decision == ApprovalDecisionEnum.APPROVE:
                state["status"] = AgentExecutionStatusEnum.APPROVED.value
                state["approval_required"] = False
            elif decision_req.decision in [ApprovalDecisionEnum.REJECT, ApprovalDecisionEnum.REQUEST_CHANGES]:
                rework_count = state.get("rework_count", 0) + 1
                state["rework_count"] = rework_count
                state["status"] = AgentExecutionStatusEnum.REWORK_REQUIRED.value
                state["rejection_reason"] = decision_req.feedback
                state["approval_status"] = None
                state["approval_required"] = False
                
                from app.schemas.approval import ReworkRecord
                rework_rec = ReworkRecord(
                    rework_id=f"rwk_{uuid.uuid4().hex[:10]}",
                    execution_id=execution_id,
                    approval_id=approval_id,
                    phase=state.get("current_phase", "ARCHITECTURE"),
                    attempt_number=rework_count,
                    feedback=decision_req.feedback or "Changes requested",
                    previous_output=state.get("architecture", {})
                )
                storage_service.save_rework_record(execution_id, rework_rec)
            elif decision_req.decision == ApprovalDecisionEnum.CANCEL:
                state["status"] = AgentExecutionStatusEnum.CANCELLED.value
        elif feedback:
            state["human_feedback"] = feedback

        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"RESUMING EXECUTION: [{execution_id}] Status={state.get('status')} Node={state.get('current_node')}")
        
        # Resume the same graph thread from checkpoint
        result_state = await self.graph.ainvoke(state, config=config)
        storage_service.save_agent_checkpoint(thread_id, result_state)
        storage_service.save_agent_execution(execution_id, result_state)
        return result_state

    async def pause_execution(self, execution_id: str) -> AgentState:
        exec_data = storage_service.get_agent_execution(execution_id)
        if not exec_data:
            raise ValueError(f"Execution '{execution_id}' not found.")
        state = dict(exec_data)
        state["status"] = AgentExecutionStatusEnum.PAUSED.value
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        storage_service.save_agent_execution(execution_id, state)
        timeline_service.record_event(
            execution_id=execution_id,
            thread_id=state.get("thread_id", execution_id),
            node=state.get("current_node", "System"),
            event="EXECUTION_PAUSED",
            status="PAUSED",
            actor="Human"
        )
        return state # type: ignore

    async def cancel_execution(self, execution_id: str, reason: str = "Cancelled by user") -> AgentState:
        exec_data = storage_service.get_agent_execution(execution_id)
        if not exec_data:
            raise ValueError(f"Execution '{execution_id}' not found.")
        state = dict(exec_data)
        state["status"] = AgentExecutionStatusEnum.CANCELLED.value
        state["errors"] = state.get("errors", []) + [reason]
        state["updated_at"] = datetime.now(timezone.utc).isoformat()
        storage_service.save_agent_execution(execution_id, state)
        timeline_service.record_event(
            execution_id=execution_id,
            thread_id=state.get("thread_id", execution_id),
            node=state.get("current_node", "System"),
            event="EXECUTION_CANCELLED",
            status="CANCELLED",
            actor="Human",
            metadata={"reason": reason}
        )
        return state # type: ignore

master_orchestrator = MasterOrchestrator()

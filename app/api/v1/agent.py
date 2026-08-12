from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from app.schemas.approval import (
    AgentExecutionCreateRequest,
    AgentResumeRequest,
    TimelineEvent
)
from app.agents.orchestrator.graph import master_orchestrator
from app.services.storage import storage_service
from app.services.timeline_service import timeline_service

router = APIRouter(prefix="/agent", tags=["Agent Orchestrator & Execution"])

@router.post("/execute", response_model=Dict[str, Any])
async def execute_agent(request: AgentExecutionCreateRequest):
    """
    Start a new durable multi-agent software engineering execution thread.
    Runs until completion or pauses at the first Human-in-the-Loop gate.
    """
    try:
        state = await master_orchestrator.start_execution(
            prompt=request.prompt,
            project_id=request.project_id,
            user_id=request.user_id,
            task_id=request.task_id
        )
        return state
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{execution_id}", response_model=Dict[str, Any])
async def get_execution_status(execution_id: str):
    """Retrieve summary execution state."""
    state = storage_service.get_agent_execution(execution_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found.")
    return {
        "execution_id": state.get("execution_id"),
        "thread_id": state.get("thread_id"),
        "status": state.get("status"),
        "current_phase": state.get("current_phase"),
        "current_node": state.get("current_node"),
        "approval_required": state.get("approval_required"),
        "approval_id": state.get("approval_id"),
        "approval_status": state.get("approval_status"),
        "rework_count": state.get("rework_count", 0),
        "created_at": state.get("created_at"),
        "updated_at": state.get("updated_at")
    }

@router.get("/{execution_id}/state", response_model=Dict[str, Any])
async def get_execution_full_state(execution_id: str):
    """Retrieve full persistent AgentState."""
    state = storage_service.get_agent_execution(execution_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Execution '{execution_id}' not found.")
    return state

@router.get("/{execution_id}/timeline", response_model=List[TimelineEvent])
async def get_execution_timeline(execution_id: str):
    """Retrieve full execution timeline events."""
    return timeline_service.get_timeline(execution_id)

@router.post("/{execution_id}/resume", response_model=Dict[str, Any])
async def resume_agent(execution_id: str, request: AgentResumeRequest):
    """
    Resume an interrupted execution thread after human decision.
    Validates approval, updates state, and continues LangGraph execution.
    """
    try:
        state = await master_orchestrator.resume_execution(
            execution_id=execution_id,
            decision_req=request.approval_decision,
            feedback=request.user_feedback
        )
        return state
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{execution_id}/pause", response_model=Dict[str, Any])
async def pause_agent(execution_id: str):
    """Pause execution at a safe workflow boundary."""
    try:
        return await master_orchestrator.pause_execution(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{execution_id}/cancel", response_model=Dict[str, Any])
async def cancel_agent(execution_id: str):
    """Cancel execution thread safely."""
    try:
        return await master_orchestrator.cancel_execution(execution_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

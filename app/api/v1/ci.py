import uuid
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from app.schemas.ci import (
    CIMonitorRequest,
    CIMonitorResponse,
    CIApprovalRequest,
    RepairActionRequest,
    CIRunStatusEnum,
    CIFailure,
    RepairPlan,
    RepairResult,
    RepairAttempt
)
from app.agents.ci.graph import ci_repair_agent
from app.services.storage import storage_service
from app.core.logging import logger

router = APIRouter(prefix="/ci", tags=["CI/CD Monitoring & Autonomous Repair"])
repairs_router = APIRouter(prefix="/repairs", tags=["Autonomous Repair System"])

@router.post("/monitor", response_model=CIMonitorResponse)
async def monitor_ci_pipeline(request: CIMonitorRequest):
    """
    Triggers the autonomous CI/CD monitoring and bounded repair workflow.
    """
    run_id = f"ci_run_{uuid.uuid4().hex[:8]}"
    session_id = f"sess_ci_{run_id}"
    
    logger.info(f"Received CI Monitor Request for Repo: {request.repository}, Branch: {request.branch}")
    
    initial_state = {
        "run_id": run_id,
        "project_id": request.project_id,
        "user_id": request.user_id,
        "repository": request.repository,
        "branch": request.branch,
        "pull_request_number": request.pull_request_number,
        "workflow_run_id": request.workflow_run_id,
        "workspace_directory": request.workspace_directory or f"generated_projects/{request.project_id}",
        "attempt_count": 1,
        "max_attempts": 3,
        "errors": []
    }
    
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        final_state = await ci_repair_agent.ainvoke(initial_state, config=config)
        
        response = CIMonitorResponse(
            run_id=run_id,
            status=final_state.get("status", CIRunStatusEnum.CI_PASSED),
            workflow_run_id=final_state.get("workflow_run_id", request.workflow_run_id or 100201),
            branch=request.branch,
            commit_sha=final_state.get("workflow_run").commit_sha if final_state.get("workflow_run") else "mock_sha",
            failed_jobs=len(final_state.get("failed_jobs", [])),
            repair_attempt=final_state.get("attempt_count", 1) - 1,
            max_attempts=3,
            failure=final_state.get("failure"),
            repair_plan=final_state.get("repair_plan"),
            repair_result=final_state.get("repair_result"),
            message="CI monitoring and autonomous repair executed successfully."
        )
        
        storage_service.save_ci_run(run_id, response)
        return response
        
    except Exception as e:
        logger.error(f"CI Monitor workflow error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"CI Monitor execution failed: {str(e)}")

@router.get("/{run_id}", response_model=CIMonitorResponse)
async def get_ci_run(run_id: str):
    """Retrieves CI monitoring run record."""
    run = storage_service.get_ci_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"CI Run ID '{run_id}' not found.")
    return run

@router.get("/{run_id}/failures")
async def get_ci_run_failures(run_id: str):
    """Retrieves failure records associated with a CI run."""
    run = storage_service.get_ci_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"CI Run ID '{run_id}' not found.")
    failure = run.failure if hasattr(run, "failure") else None
    return {"run_id": run_id, "failures": [failure] if failure else []}

@router.post("/{run_id}/approve", response_model=CIMonitorResponse)
async def approve_ci_repair(run_id: str, approval: CIApprovalRequest):
    """Lead DevOps approval for high-risk autonomous repairs."""
    run = storage_service.get_ci_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"CI Run ID '{run_id}' not found.")
        
    run.status = CIRunStatusEnum.REPAIRING
    run.message = f"Repair approved by {approval.reviewer_name}: {approval.notes or 'Proceed with repair'}"
    storage_service.save_ci_run(run_id, run)
    return run

@router.post("/{run_id}/reject", response_model=CIMonitorResponse)
async def reject_ci_repair(run_id: str, approval: CIApprovalRequest):
    """Rejects the autonomous repair and marks CI run as BLOCKED."""
    run = storage_service.get_ci_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"CI Run ID '{run_id}' not found.")
        
    run.status = CIRunStatusEnum.BLOCKED
    run.message = f"Repair rejected by {approval.reviewer_name}: {approval.notes or 'Manual triage requested'}"
    storage_service.save_ci_run(run_id, run)
    return run

# Repairs Router Endpoints
@repairs_router.get("/{repair_id}")
async def get_repair_plan(repair_id: str):
    """Retrieves repair plan and result details by Repair ID."""
    plan = storage_service.get_repair_plan(repair_id)
    result = storage_service.get_repair_result(repair_id)
    if not plan and not result:
        raise HTTPException(status_code=404, detail=f"Repair ID '{repair_id}' not found.")
    return {
        "repair_id": repair_id,
        "plan": plan,
        "result": result
    }

@repairs_router.get("/{repair_id}/attempts")
async def get_repair_attempts(repair_id: str):
    """Retrieves list of attempts executed for a Repair ID."""
    attempts = storage_service.get_repair_attempts(repair_id)
    return {
        "repair_id": repair_id,
        "total_attempts": len(attempts),
        "attempts": attempts
    }

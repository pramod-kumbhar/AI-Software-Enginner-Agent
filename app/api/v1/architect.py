import uuid
from fastapi import APIRouter, HTTPException
from app.schemas.architecture import (
    ArchitectInputRequest,
    ArchitectResponse,
    ApprovalActionRequest,
    ApprovalStatusEnum
)
from app.agents.architect.graph import architect_agent
from app.services.storage import storage_service
from app.core.logging import logger

router = APIRouter(prefix="/architect", tags=["Architect Agent"])

@router.post("/generate", response_model=ArchitectResponse)
async def generate_architecture(request: ArchitectInputRequest):
    """
    Triggers the Architect Agent workflow to convert an approved plan into software architecture.
    """
    arch_task_id = str(uuid.uuid4())
    session_id = f"arch_session_{arch_task_id}"
    
    # 1. Resolve planner output
    plan = request.planner_output
    if not plan and request.planner_task_id:
        plan = storage_service.get_plan(request.planner_task_id)
        
    if not plan:
        raise HTTPException(
            status_code=400,
            detail="Planner output missing. Provide 'planner_task_id' or 'planner_output' in request."
        )
        
    logger.info(f"Received architecture generation request for Task ID: {arch_task_id}")
    
    initial_state = {
        "user_id": request.user_id or "user_pramod_01",
        "project_id": request.project_id or "proj_default_01",
        "planner_task_id": request.planner_task_id or "inline_plan",
        "architect_task_id": arch_task_id,
        "session_id": session_id,
        "planner_output": plan,
        "retry_count": 0
    }
    
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        final_state = await architect_agent.ainvoke(initial_state, config=config)
        final_arch = final_state.get("final_architecture")
        
        response = ArchitectResponse(
            architect_task_id=arch_task_id,
            planner_task_id=request.planner_task_id,
            project_id=request.project_id or "proj_default_01",
            architecture_status=final_state.get("architecture_status", "UNKNOWN"),
            human_approval=final_arch.human_approval if final_arch else final_state.get("human_approval"),
            architecture=final_arch,
            validation_results=final_state.get("validation_results"),
            errors=final_state.get("errors", []),
            retry_count=final_state.get("retry_count", 0)
        )
        
        return response
    except Exception as e:
        logger.error(f"Architecture generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Architecture execution failed: {str(e)}")

@router.get("/{architect_task_id}", response_model=ArchitectResponse)
async def get_architecture(architect_task_id: str):
    """Retrieves generated architecture by Task ID."""
    arch = storage_service.get_architecture(architect_task_id)
    if not arch:
        raise HTTPException(status_code=404, detail="Architecture Task ID not found")
        
    return ArchitectResponse(
        architect_task_id=architect_task_id,
        project_id=arch.project_information.project_slug,
        architecture_status="COMPLETED",
        human_approval=arch.human_approval,
        architecture=arch,
        validation_results=arch.validation_results
    )

@router.post("/{architect_task_id}/approve", response_model=ArchitectResponse)
async def approve_architecture(architect_task_id: str, action: ApprovalActionRequest):
    """Approves the architecture for Developer Agent code generation."""
    success = storage_service.update_architecture_approval(
        task_id=architect_task_id,
        status=ApprovalStatusEnum.APPROVED,
        reviewer=action.reviewer_name,
        notes=action.notes
    )
    if not success:
        raise HTTPException(status_code=404, detail="Architecture Task ID not found")
        
    arch = storage_service.get_architecture(architect_task_id)
    return ArchitectResponse(
        architect_task_id=architect_task_id,
        project_id=arch.project_information.project_slug,
        architecture_status="APPROVED",
        human_approval=arch.human_approval,
        architecture=arch
    )

@router.post("/{architect_task_id}/reject", response_model=ArchitectResponse)
async def reject_architecture(architect_task_id: str, action: ApprovalActionRequest):
    """Rejects the architecture."""
    success = storage_service.update_architecture_approval(
        task_id=architect_task_id,
        status=ApprovalStatusEnum.REJECTED,
        reviewer=action.reviewer_name,
        notes=action.notes or "Architecture rejected by human reviewer."
    )
    if not success:
        raise HTTPException(status_code=404, detail="Architecture Task ID not found")
        
    arch = storage_service.get_architecture(architect_task_id)
    return ArchitectResponse(
        architect_task_id=architect_task_id,
        project_id=arch.project_information.project_slug,
        architecture_status="REJECTED",
        human_approval=arch.human_approval,
        architecture=arch
    )

@router.post("/{architect_task_id}/revise", response_model=ArchitectResponse)
async def revise_architecture(architect_task_id: str, action: ApprovalActionRequest):
    """Requests revision of the architecture."""
    success = storage_service.update_architecture_approval(
        task_id=architect_task_id,
        status=ApprovalStatusEnum.REVISION_REQUIRED,
        reviewer=action.reviewer_name,
        notes=action.notes
    )
    if not success:
        raise HTTPException(status_code=404, detail="Architecture Task ID not found")
        
    arch = storage_service.get_architecture(architect_task_id)
    return ArchitectResponse(
        architect_task_id=architect_task_id,
        project_id=arch.project_information.project_slug,
        architecture_status="REVISION_REQUIRED",
        human_approval=arch.human_approval,
        architecture=arch
    )

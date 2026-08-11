import uuid
from fastapi import APIRouter, HTTPException
from app.schemas.developer import (
    DeveloperInputRequest,
    DeveloperResponse
)
from app.schemas.architecture import ApprovalActionRequest, ApprovalStatusEnum
from app.agents.developer.graph import developer_agent
from app.services.storage import storage_service
from app.core.logging import logger

router = APIRouter(prefix="/developer", tags=["Developer Agent"])

@router.post("/generate", response_model=DeveloperResponse)
async def generate_implementation(request: DeveloperInputRequest):
    """
    Triggers Developer Agent to generate complete source code and tests from approved architecture.
    """
    dev_task_id = str(uuid.uuid4())
    session_id = f"dev_session_{dev_task_id}"
    
    # 1. Resolve architecture
    arch = request.approved_architecture
    if not arch and request.architect_task_id:
        arch = storage_service.get_architecture(request.architect_task_id)
        
    if not arch:
        raise HTTPException(
            status_code=400,
            detail="Architecture missing. Provide 'architect_task_id' or 'approved_architecture' in request."
        )
        
    ws_dir = request.workspace_directory or f"generated_projects/{dev_task_id}"
    logger.info(f"Received code generation request for Dev Task ID: {dev_task_id}")
    
    initial_state = {
        "user_id": request.user_id or "user_pramod_01",
        "project_id": request.project_id or "proj_default_01",
        "architect_task_id": request.architect_task_id or "inline_arch",
        "developer_task_id": dev_task_id,
        "session_id": session_id,
        "approved_architecture": arch,
        "workspace_directory": ws_dir,
        "retry_count": 0
    }
    
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        final_state = await developer_agent.ainvoke(initial_state, config=config)
        report = final_state.get("implementation_report")
        
        response = DeveloperResponse(
            developer_task_id=dev_task_id,
            architect_task_id=request.architect_task_id or "inline_arch",
            project_id=request.project_id or "proj_default_01",
            implementation_status=final_state.get("implementation_status", "UNKNOWN"),
            human_approval=report.human_approval if report else final_state.get("human_approval"),
            implementation_report=report,
            generated_files=[f.file_path for f in final_state.get("generated_files", [])],
            test_results=final_state.get("test_results"),
            errors=final_state.get("errors", []),
            retry_count=final_state.get("retry_count", 0)
        )
        
        return response
    except Exception as e:
        logger.error(f"Developer generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Code generation failed: {str(e)}")

@router.get("/{developer_task_id}", response_model=DeveloperResponse)
async def get_developer_run(developer_task_id: str):
    """Retrieves generated implementation by Developer Task ID."""
    report = storage_service.get_developer_run(developer_task_id)
    if not report:
        raise HTTPException(status_code=404, detail="Developer Task ID not found")
        
    return DeveloperResponse(
        developer_task_id=developer_task_id,
        architect_task_id=report.architect_task_id,
        project_id=report.project_slug,
        implementation_status=report.implementation_status,
        human_approval=report.human_approval,
        implementation_report=report,
        generated_files=report.files_created
    )

@router.post("/{developer_task_id}/approve", response_model=DeveloperResponse)
async def approve_implementation(developer_task_id: str, action: ApprovalActionRequest):
    """Approves implementation for deployment."""
    success = storage_service.update_developer_approval(
        task_id=developer_task_id,
        status=ApprovalStatusEnum.APPROVED,
        reviewer=action.reviewer_name,
        notes=action.notes
    )
    if not success:
        raise HTTPException(status_code=404, detail="Developer Task ID not found")
        
    report = storage_service.get_developer_run(developer_task_id)
    return DeveloperResponse(
        developer_task_id=developer_task_id,
        architect_task_id=report.architect_task_id,
        project_id=report.project_slug,
        implementation_status="APPROVED",
        human_approval=report.human_approval,
        implementation_report=report
    )

@router.post("/{developer_task_id}/reject", response_model=DeveloperResponse)
async def reject_implementation(developer_task_id: str, action: ApprovalActionRequest):
    """Rejects implementation."""
    success = storage_service.update_developer_approval(
        task_id=developer_task_id,
        status=ApprovalStatusEnum.REJECTED,
        reviewer=action.reviewer_name,
        notes=action.notes or "Implementation rejected by reviewer."
    )
    if not success:
        raise HTTPException(status_code=404, detail="Developer Task ID not found")
        
    report = storage_service.get_developer_run(developer_task_id)
    return DeveloperResponse(
        developer_task_id=developer_task_id,
        architect_task_id=report.architect_task_id,
        project_id=report.project_slug,
        implementation_status="REJECTED",
        human_approval=report.human_approval,
        implementation_report=report
    )

@router.post("/{developer_task_id}/revise", response_model=DeveloperResponse)
async def revise_implementation(developer_task_id: str, action: ApprovalActionRequest):
    """Requests code revision."""
    success = storage_service.update_developer_approval(
        task_id=developer_task_id,
        status=ApprovalStatusEnum.REVISION_REQUIRED,
        reviewer=action.reviewer_name,
        notes=action.notes
    )
    if not success:
        raise HTTPException(status_code=404, detail="Developer Task ID not found")
        
    report = storage_service.get_developer_run(developer_task_id)
    return DeveloperResponse(
        developer_task_id=developer_task_id,
        architect_task_id=report.architect_task_id,
        project_id=report.project_slug,
        implementation_status="REVISION_REQUIRED",
        human_approval=report.human_approval,
        implementation_report=report
    )

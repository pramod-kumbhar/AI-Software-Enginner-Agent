from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from app.schemas.approval import (
    ApprovalRequest,
    ApprovalDecisionRequest,
    ApprovalStatusEnum,
    ApprovalDecisionEnum,
    ReviewerRoleEnum
)
from app.services.approval_service import (
    approval_service,
    ApprovalServiceError,
    UnauthorizedApproverError,
    SeparationOfDutiesError,
    StaleApprovalError,
    ApprovalExpiredError
)

router = APIRouter(prefix="/approvals", tags=["Human Approvals"])

@router.get("", response_model=List[ApprovalRequest])
async def list_approvals(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    status: Optional[ApprovalStatusEnum] = Query(None, description="Filter by approval status")
):
    """List all human approval requests matching filters."""
    return approval_service.list_approvals(project_id=project_id, status=status)

@router.get("/{approval_id}", response_model=ApprovalRequest)
async def get_approval(approval_id: str):
    """Retrieve specific approval request details."""
    req = approval_service.get_approval(approval_id)
    if not req:
        raise HTTPException(status_code=404, detail=f"Approval request '{approval_id}' not found.")
    return req

@router.post("/{approval_id}/approve", response_model=ApprovalRequest)
async def approve_request(approval_id: str, decision_req: ApprovalDecisionRequest):
    """Approve a pending human authorization request."""
    decision_req.decision = ApprovalDecisionEnum.APPROVE
    try:
        return approval_service.resolve_approval(approval_id, decision_req)
    except UnauthorizedApproverError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except SeparationOfDutiesError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except StaleApprovalError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ApprovalExpiredError as e:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e))
    except ApprovalServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{approval_id}/reject", response_model=ApprovalRequest)
async def reject_request(approval_id: str, decision_req: ApprovalDecisionRequest):
    """Reject a pending human authorization request."""
    decision_req.decision = ApprovalDecisionEnum.REJECT
    try:
        return approval_service.resolve_approval(approval_id, decision_req)
    except UnauthorizedApproverError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ApprovalServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{approval_id}/request-changes", response_model=ApprovalRequest)
async def request_changes(approval_id: str, decision_req: ApprovalDecisionRequest):
    """Request structured rework/changes from the agent node."""
    decision_req.decision = ApprovalDecisionEnum.REQUEST_CHANGES
    try:
        return approval_service.resolve_approval(approval_id, decision_req)
    except UnauthorizedApproverError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ApprovalServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/{approval_id}/cancel", response_model=ApprovalRequest)
async def cancel_approval(approval_id: str, decision_req: ApprovalDecisionRequest):
    """Cancel a pending authorization request safely."""
    decision_req.decision = ApprovalDecisionEnum.CANCEL
    try:
        return approval_service.resolve_approval(approval_id, decision_req)
    except ApprovalServiceError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/projects/{project_id}", response_model=List[ApprovalRequest])
async def list_project_approvals(project_id: str):
    """List all approval requests for a specific project."""
    return approval_service.list_approvals(project_id=project_id)

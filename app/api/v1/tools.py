import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.mcp.schemas import (
    ToolDefinition,
    ToolRequest,
    ToolResult,
    ToolExecutionStatusEnum,
    ToolCategoryEnum
)
from app.mcp.registry import tool_registry
from app.mcp.executor import tool_executor
from app.services.storage import storage_service
from app.core.logging import logger

router = APIRouter(prefix="/tools", tags=["Tool & MCP Layer"])

@router.get("", response_model=List[ToolDefinition])
async def list_available_tools(
    role: Optional[str] = Query("DEVELOPER", description="Caller role to filter discoverable tools"),
    category: Optional[ToolCategoryEnum] = Query(None, description="Filter by tool category")
):
    """Lists discoverable tools filtered by caller role and category."""
    return tool_registry.list_tools(role=role, category=category)

@router.post("/execute", response_model=ToolResult)
async def execute_tool(request: ToolRequest):
    """
    Executes a registered tool through the central ToolExecutor with authorization,
    safety checks, and audit logging.
    """
    logger.info(f"API Tool Execution Request: [{request.tool_name}] (Req ID: {request.request_id})")
    result = await tool_executor.execute(request)
    return result

@router.get("/{request_id}", response_model=ToolResult)
async def get_tool_execution_status(request_id: str):
    """Retrieves tool execution result and status by request ID."""
    stored = storage_service.get_tool_request(request_id)
    if not stored:
        raise HTTPException(status_code=404, detail=f"Tool request '{request_id}' not found.")
    return stored

@router.post("/{request_id}/approve", response_model=ToolResult)
async def approve_tool_request(request_id: str, reviewer_name: str = "Lead_Reviewer"):
    """
    Approves a PENDING dangerous/high-risk tool invocation and executes it immediately.
    """
    stored = storage_service.get_tool_request(request_id)
    if not stored:
        raise HTTPException(status_code=404, detail=f"Tool request '{request_id}' not found.")
        
    audit_logs = storage_service.get_audit_logs(request_id=request_id)
    if not audit_logs:
        raise HTTPException(status_code=400, detail="No audit log found for approval request.")
        
    last_log = audit_logs[-1]
    args = last_log.get("metadata", {}).get("sanitized_arguments", {})
    
    # Re-execute with approval token
    approval_token = f"approved_{uuid.uuid4().hex[:12]}"
    auth_ctx = {
        "user_id": last_log.get("user_id", "default"),
        "project_id": last_log.get("project_id", "default"),
        "agent_name": last_log.get("agent_name", "DeveloperAgent"),
        "role": "ADMIN",
        "approval_token": approval_token,
        "approved_by": reviewer_name
    }
    
    approved_req = ToolRequest(
        request_id=request_id,
        tool_name=last_log["tool_name"],
        arguments=args,
        authorization_context=auth_ctx
    )
    
    result = await tool_executor.execute(approved_req)
    return result

@router.post("/{request_id}/reject", response_model=ToolResult)
async def reject_tool_request(request_id: str, reason: str = "Rejected by human reviewer"):
    """Rejects a PENDING tool invocation."""
    stored = storage_service.get_tool_request(request_id)
    if not stored:
        raise HTTPException(status_code=404, detail=f"Tool request '{request_id}' not found.")
        
    result = ToolResult(
        request_id=request_id,
        tool_name=stored.get("tool_name", "unknown"),
        status=ToolExecutionStatusEnum.REJECTED,
        error=f"Tool execution rejected: {reason}",
        duration_ms=0.0
    )
    storage_service.save_tool_request(request_id, result.model_dump())
    return result

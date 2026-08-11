import time
import inspect
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.mcp.schemas import (
    ToolRequest,
    ToolResult,
    ToolExecutionStatusEnum,
    RiskLevelEnum
)
from app.mcp.registry import tool_registry
from app.mcp.authorization import tool_authorizer
from app.mcp.audit import tool_audit_logger
from app.services.storage import storage_service
from app.core.config import settings
from app.core.prompt_guard import prompt_guard
from app.core.secret_scanner import secret_scanner


class ToolExecutor:
    """
    Central execution engine for all tool invocations.
    Guarantees authorization, safety checks, validation, audit logging, and structured outputs.
    """
    
    @classmethod
    async def execute(cls, request: ToolRequest) -> ToolResult:
        start_time = time.time()
        started_at = datetime.now(timezone.utc).isoformat()
        
        # 1. Look up tool definition
        tool_def = tool_registry.get_tool(request.tool_name)
        if not tool_def:
            duration = round((time.time() - start_time) * 1000, 2)
            result = ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                status=ToolExecutionStatusEnum.FAILED,
                error=f"Tool '{request.tool_name}' is not registered in the system.",
                duration_ms=duration
            )
            tool_audit_logger.record_execution(request, result, RiskLevelEnum.READ_ONLY, started_at)
            storage_service.save_tool_request(request.request_id, result.model_dump())
            return result
            
        handler = tool_registry.get_handler(request.tool_name)
        if not handler:
            duration = round((time.time() - start_time) * 1000, 2)
            result = ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                status=ToolExecutionStatusEnum.FAILED,
                error=f"Handler for tool '{request.tool_name}' is missing.",
                duration_ms=duration
            )
            tool_audit_logger.record_execution(request, result, tool_def.risk_level, started_at)
            storage_service.save_tool_request(request.request_id, result.model_dump())
            return result

        # 2. Authorize execution
        is_authorized, auth_error = tool_authorizer.authorize(tool_def, request)
        if not is_authorized:
            duration = round((time.time() - start_time) * 1000, 2)
            status = ToolExecutionStatusEnum.PENDING if "approval" in (auth_error or "").lower() else ToolExecutionStatusEnum.BLOCKED
            result = ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                status=status,
                error=auth_error,
                duration_ms=duration
            )
            tool_audit_logger.record_execution(request, result, tool_def.risk_level, started_at)
            storage_service.save_tool_request(request.request_id, result.model_dump())
            return result

        # 3. Validate arguments against schema requirements
        required_params = tool_def.input_schema.get("required", [])
        missing_params = [p for p in required_params if p not in request.arguments]
        if missing_params:
            duration = round((time.time() - start_time) * 1000, 2)
            result = ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                status=ToolExecutionStatusEnum.FAILED,
                error=f"Missing required parameters: {', '.join(missing_params)}",
                duration_ms=duration
            )
            tool_audit_logger.record_execution(request, result, tool_def.risk_level, started_at)
            storage_service.save_tool_request(request.request_id, result.model_dump())
            return result

        # 4. Prompt Injection Scan on String Arguments
        for arg_k, arg_v in request.arguments.items():
            if isinstance(arg_v, str):
                pi_check = prompt_guard.scan_content(arg_v, source="TOOL_INPUT")
                if pi_check["is_blocked"] and tool_def.risk_level != RiskLevelEnum.READ_ONLY:
                    duration = round((time.time() - start_time) * 1000, 2)
                    result = ToolResult(
                        request_id=request.request_id,
                        tool_name=request.tool_name,
                        status=ToolExecutionStatusEnum.BLOCKED,
                        error=f"PROMPT INJECTION BLOCKED: Prohibited instruction pattern detected in argument '{arg_k}'.",
                        duration_ms=duration
                    )
                    tool_audit_logger.record_execution(request, result, tool_def.risk_level, started_at)
                    storage_service.save_tool_request(request.request_id, result.model_dump())
                    return result

        # 5. Inject workspace context if needed
        exec_args = dict(request.arguments)
        if "workspace_root" in inspect.signature(handler).parameters and "workspace_root" not in exec_args:
            exec_args["workspace_root"] = request.authorization_context.workspace_root or settings.WORKSPACE_BASE_DIR

        # 6. Execute handler safely
        try:
            if inspect.iscoroutinefunction(handler):
                handler_result = await asyncio.wait_for(
                    handler(**exec_args),
                    timeout=settings.TOOL_TIMEOUT_SECONDS
                )
            else:
                handler_result = handler(**exec_args)

            # Sanitize output from hardcoded secrets
            if isinstance(handler_result, str):
                handler_result = secret_scanner.mask_secret(handler_result)
            elif isinstance(handler_result, dict):
                handler_result = {k: secret_scanner.mask_secret(v) if isinstance(v, str) else v for k, v in handler_result.items()}

            duration = round((time.time() - start_time) * 1000, 2)
            result = ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                status=ToolExecutionStatusEnum.SUCCESS,
                result=handler_result,
                duration_ms=duration,
                metadata={"risk_level": tool_def.risk_level.value}
            )
        except asyncio.TimeoutError:
            duration = round((time.time() - start_time) * 1000, 2)
            result = ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                status=ToolExecutionStatusEnum.FAILED,
                error=f"Tool execution timed out after {settings.TOOL_TIMEOUT_SECONDS}s.",
                duration_ms=duration
            )
        except Exception as ex:
            duration = round((time.time() - start_time) * 1000, 2)
            result = ToolResult(
                request_id=request.request_id,
                tool_name=request.tool_name,
                status=ToolExecutionStatusEnum.FAILED,
                error=f"{type(ex).__name__}: {str(ex)}",
                duration_ms=duration
            )

        # 7. Audit log and persist
        tool_audit_logger.record_execution(request, result, tool_def.risk_level, started_at)
        storage_service.save_tool_request(request.request_id, result.model_dump())
        return result

tool_executor = ToolExecutor()


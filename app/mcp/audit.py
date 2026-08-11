import hashlib
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from app.mcp.schemas import AuditLogRecord, ToolRequest, ToolResult, RiskLevelEnum
from app.services.storage import storage_service
from app.core.logging import logger
from app.core.security import SecretMasker

class ToolAuditLogger:
    """
    Logs structured, zero-leakage audit records for all tool executions.
    """
    @classmethod
    def record_execution(
        cls,
        request: ToolRequest,
        result: ToolResult,
        risk_level: RiskLevelEnum,
        started_at: str
    ) -> AuditLogRecord:
        completed_at = datetime.now(timezone.utc).isoformat()
        
        # 1. Sanitize arguments and compute deterministic hash
        sanitized_args = SecretMasker.sanitize_dict(request.arguments)
        args_str = json.dumps(sanitized_args, sort_keys=True)
        args_hash = hashlib.sha256(args_str.encode("utf-8")).hexdigest()
        
        # 2. Mask error message if present
        sanitized_error = SecretMasker.mask_text(result.error) if result.error else None
        
        record = AuditLogRecord(
            request_id=request.request_id,
            user_id=request.authorization_context.user_id,
            project_id=request.authorization_context.project_id,
            agent_name=request.authorization_context.agent_name,
            tool_name=request.tool_name,
            risk_level=risk_level,
            arguments_hash=args_hash,
            approval_status="APPROVED" if request.authorization_context.approval_token else "NONE",
            execution_status=result.status.value,
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=result.duration_ms,
            error_type=sanitized_error,
            metadata={"sanitized_arguments": sanitized_args}
        )
        
        # Save to persistent audit store
        storage_service.append_audit_log(record.model_dump())
        logger.info(
            f"TOOL AUDIT: [{request.tool_name}] status={result.status.value} duration={result.duration_ms}ms risk={risk_level.value}",
            extra={"tool_name": request.tool_name, "request_id": request.request_id}
        )
        
        return record

tool_audit_logger = ToolAuditLogger()

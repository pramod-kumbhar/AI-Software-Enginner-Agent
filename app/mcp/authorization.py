import re
from typing import Tuple, Optional
from app.mcp.schemas import (
    ToolDefinition,
    ToolRequest,
    RiskLevelEnum,
    ToolAuthorizationContext
)
from app.core.config import settings

class AuthorizationError(Exception):
    """Raised when an agent or user is not authorized to invoke a tool."""
    pass

class ToolAuthorizationManager:
    """
    Multi-factor authorization guard for tool execution.
    Audits roles, risk levels, human approvals, and operational boundaries.
    """
    
    CRITICAL_BLOCKED_TOOLS = {
        "git.delete_branch",
        "github.merge_pull_request",
        "system.execute_raw_shell",
        "filesystem.delete_workspace"
    }

    @classmethod
    def authorize(cls, tool_def: ToolDefinition, request: ToolRequest) -> Tuple[bool, Optional[str]]:
        context = request.authorization_context
        
        # 1. Block globally forbidden / dangerous operations in Day 10
        if tool_def.name in cls.CRITICAL_BLOCKED_TOOLS or tool_def.risk_level == RiskLevelEnum.CRITICAL:
            return False, f"Tool '{tool_def.name}' is categorized as CRITICAL and is strictly blocked."

        # 2. Check Agent Role Permission
        if context.role not in tool_def.allowed_roles and "ALL" not in tool_def.allowed_roles:
            return False, f"Role '{context.role}' (Agent: {context.agent_name}) is unauthorized for '{tool_def.name}'."

        # 3. Check Risk Level and Human Approval Requirement
        if tool_def.requires_approval or (settings.REQUIRE_HUMAN_APPROVAL_FOR_HIGH_RISK and tool_def.risk_level == RiskLevelEnum.HIGH_RISK):
            if not context.approval_token and not context.approved_by:
                return False, f"Tool '{tool_def.name}' ({tool_def.risk_level.value}) requires explicit human approval."

        # 4. Check Filesystem Workspace Containment (if workspace path is passed in args)
        file_path_arg = request.arguments.get("file_path") or request.arguments.get("path") or request.arguments.get("directory")
        if file_path_arg and isinstance(file_path_arg, str):
            if ".." in file_path_arg or file_path_arg.startswith("/") or re.match(r'^[a-zA-Z]:', file_path_arg):
                # Normalized relative check
                clean = file_path_arg.replace("\\", "/").strip()
                if clean.startswith("/") or ".." in clean or (len(clean) > 1 and clean[1] == ":"):
                    return False, f"Path traversal attempt detected: '{file_path_arg}'"

        return True, None

tool_authorizer = ToolAuthorizationManager()

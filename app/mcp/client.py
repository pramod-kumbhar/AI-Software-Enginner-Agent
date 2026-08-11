import uuid
from typing import Dict, Any, List, Optional
from app.mcp.schemas import (
    ToolRequest,
    ToolResult,
    ToolAuthorizationContext,
    ToolDefinition,
    MCPCallToolRequest,
    MCPCallToolResult
)
from app.mcp.registry import tool_registry
from app.mcp.executor import tool_executor
from app.mcp.server import mcp_server

class MCPClient:
    """
    Client abstraction allowing agents (Developer, QA, Architect, CI Monitor) to discover and execute tools.
    Encapsulates role-based authorization context and idempotency request tracking.
    """
    def __init__(
        self,
        agent_name: str = "DeveloperAgent",
        role: str = "DEVELOPER",
        project_id: str = "default_proj",
        user_id: str = "user_default",
        workspace_root: Optional[str] = None
    ):
        self.context = ToolAuthorizationContext(
            agent_name=agent_name,
            role=role,
            project_id=project_id,
            user_id=user_id,
            workspace_root=workspace_root
        )

    def discover_tools(self) -> List[ToolDefinition]:
        """Discovers all tools permitted for this client's role."""
        return tool_registry.list_tools(role=self.context.role)

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any], approval_token: Optional[str] = None) -> ToolResult:
        """Executes a tool with the client's ambient authorization context."""
        req_id = str(uuid.uuid4())
        ctx = self.context.model_copy()
        if approval_token:
            ctx.approval_token = approval_token
            ctx.approved_by = "Human_Reviewer"
            
        request = ToolRequest(
            request_id=req_id,
            tool_name=tool_name,
            arguments=arguments,
            authorization_context=ctx
        )
        return await tool_executor.execute(request)

    async def call_mcp_raw(self, tool_name: str, arguments: Dict[str, Any]) -> MCPCallToolResult:
        """Invokes the MCP server via the standard MCP protocol format."""
        mcp_req = MCPCallToolRequest(name=tool_name, arguments=arguments, context=self.context)
        return await mcp_server.call_tool(mcp_req)

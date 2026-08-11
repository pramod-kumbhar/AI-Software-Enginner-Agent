from typing import Dict, Any, List, Optional
from app.mcp.schemas import (
    MCPListToolsResult,
    MCPCallToolRequest,
    MCPCallToolResult,
    ToolAuthorizationContext
)
from app.mcp.registry import tool_registry
from app.mcp.executor import tool_executor
from app.mcp.adapter import MCPAdapter

class MCPServer:
    """
    Stateless Model Context Protocol (MCP) server implementation adhering to latest MCP standards.
    Exposes safe tool discovery and controlled execution via central ToolExecutor.
    """
    
    @classmethod
    def list_tools(cls, role: Optional[str] = None) -> MCPListToolsResult:
        """Exposes discoverable tools filtered by caller role."""
        tools = tool_registry.list_tools(role=role)
        return MCPAdapter.to_mcp_list_tools_result(tools)

    @classmethod
    async def call_tool(cls, request: MCPCallToolRequest) -> MCPCallToolResult:
        """Processes an MCP call_tool request via ToolExecutor."""
        tool_req = MCPAdapter.from_mcp_call_request(request)
        tool_res = await tool_executor.execute(tool_req)
        return MCPAdapter.to_mcp_call_result(tool_res)

mcp_server = MCPServer()

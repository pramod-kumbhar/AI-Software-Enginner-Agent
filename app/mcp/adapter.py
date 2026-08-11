import json
import uuid
from typing import Dict, Any, List
from app.mcp.schemas import (
    ToolDefinition,
    ToolRequest,
    ToolResult,
    ToolAuthorizationContext,
    MCPToolInfo,
    MCPListToolsResult,
    MCPCallToolRequest,
    MCPCallToolResult,
    MCPContentItem
)

class MCPAdapter:
    """
    Stateless protocol adapter translating between MCP JSON-RPC protocol representations
    and internal ToolExecutor Request/Result models.
    """
    
    @staticmethod
    def to_mcp_tool_info(tool_def: ToolDefinition) -> MCPToolInfo:
        return MCPToolInfo(
            name=tool_def.name,
            description=f"[{tool_def.risk_level.value}] {tool_def.description}",
            inputSchema=tool_def.input_schema
        )

    @staticmethod
    def to_mcp_list_tools_result(tools: List[ToolDefinition]) -> MCPListToolsResult:
        mcp_tools = [MCPAdapter.to_mcp_tool_info(t) for t in tools]
        return MCPListToolsResult(tools=mcp_tools)

    @staticmethod
    def from_mcp_call_request(call_req: MCPCallToolRequest) -> ToolRequest:
        req_id = str(uuid.uuid4())
        context = call_req.context or ToolAuthorizationContext()
        return ToolRequest(
            request_id=req_id,
            tool_name=call_req.name,
            arguments=call_req.arguments,
            authorization_context=context
        )

    @staticmethod
    def to_mcp_call_result(tool_res: ToolResult) -> MCPCallToolResult:
        if tool_res.error:
            content = [MCPContentItem(type="text", text=f"ERROR: {tool_res.error}")]
            is_error = True
        else:
            text_repr = json.dumps(tool_res.result, indent=2) if isinstance(tool_res.result, (dict, list)) else str(tool_res.result)
            content = [MCPContentItem(type="text", text=text_repr)]
            is_error = False
            
        return MCPCallToolResult(
            content=content,
            isError=is_error,
            metadata={
                "request_id": tool_res.request_id,
                "tool_name": tool_res.tool_name,
                "status": tool_res.status.value,
                "duration_ms": tool_res.duration_ms
            }
        )

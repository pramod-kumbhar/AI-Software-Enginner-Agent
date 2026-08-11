import pytest
import asyncio
import tempfile
from app.mcp.server import mcp_server
from app.mcp.client import MCPClient
from app.mcp.schemas import MCPCallToolRequest, ToolExecutionStatusEnum

def test_mcp_server_protocol():
    async def _run():
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. List tools via MCP
            list_res = mcp_server.list_tools(role="DEVELOPER")
            assert len(list_res.tools) >= 10
            
            # 2. Call tool via MCP server
            call_req = MCPCallToolRequest(
                name="filesystem.create_file",
                arguments={"file_path": "mcp_file.py", "content": "print('MCP Standard')\n", "workspace_root": tmpdir}
            )
            call_res = await mcp_server.call_tool(call_req)
            assert call_res.isError is False
            assert len(call_res.content) > 0

    asyncio.run(_run())

def test_mcp_client_abstraction():
    async def _run():
        with tempfile.TemporaryDirectory() as tmpdir:
            client = MCPClient(
                agent_name="DeveloperAgent",
                role="DEVELOPER",
                project_id="proj_mcp_test",
                user_id="user_mcp_test",
                workspace_root=tmpdir
            )
            
            # Discover tools
            tools = client.discover_tools()
            assert len(tools) >= 10
            
            # Call tool
            res = await client.call_tool(
                "filesystem.create_file",
                {"file_path": "app.py", "content": "x = 42\n"}
            )
            assert res.status == ToolExecutionStatusEnum.SUCCESS
            
            read_res = await client.call_tool("filesystem.read_file", {"file_path": "app.py"})
            assert read_res.status == ToolExecutionStatusEnum.SUCCESS
            assert "x = 42" in read_res.result["content"]

    asyncio.run(_run())

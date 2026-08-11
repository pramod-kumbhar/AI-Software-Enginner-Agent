import pytest
import asyncio
import tempfile
from app.mcp.registry import tool_registry
from app.mcp.executor import tool_executor
from app.mcp.schemas import (
    ToolRequest,
    ToolAuthorizationContext,
    ToolExecutionStatusEnum,
    RiskLevelEnum
)

def test_tool_registry_and_discovery():
    tools = tool_registry.list_tools()
    assert len(tools) >= 15
    
    fs_read = tool_registry.get_tool("filesystem.read_file")
    assert fs_read is not None
    assert fs_read.risk_level == RiskLevelEnum.READ_ONLY
    
    dev_tools = tool_registry.list_tools(role="DEVELOPER")
    qa_tools = tool_registry.list_tools(role="QA")
    
    assert any(t.name == "filesystem.create_file" for t in dev_tools)
    assert not any(t.name == "filesystem.create_file" for t in qa_tools) # QA cannot create files

def test_tool_executor_safe_invocation():
    async def _run():
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Create file via tool executor
            create_req = ToolRequest(
                request_id="req_001",
                tool_name="filesystem.create_file",
                arguments={"file_path": "test.txt", "content": "Hello MCP!"},
                authorization_context=ToolAuthorizationContext(
                    agent_name="DeveloperAgent",
                    role="DEVELOPER",
                    workspace_root=tmpdir
                )
            )
            res1 = await tool_executor.execute(create_req)
            assert res1.status == ToolExecutionStatusEnum.SUCCESS
            assert res1.result["created"] is True
            
            # 2. Read file via tool executor
            read_req = ToolRequest(
                request_id="req_002",
                tool_name="filesystem.read_file",
                arguments={"file_path": "test.txt"},
                authorization_context=ToolAuthorizationContext(
                    agent_name="DeveloperAgent",
                    role="DEVELOPER",
                    workspace_root=tmpdir
                )
            )
            res2 = await tool_executor.execute(read_req)
            assert res2.status == ToolExecutionStatusEnum.SUCCESS
            assert "Hello MCP!" in res2.result["content"]

    asyncio.run(_run())

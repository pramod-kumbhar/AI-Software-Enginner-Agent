import pytest
import asyncio
from app.mcp.executor import tool_executor
from app.mcp.schemas import (
    ToolRequest,
    ToolAuthorizationContext,
    ToolExecutionStatusEnum
)
from app.mcp.audit import SecretMasker
from app.services.storage import storage_service

def test_unauthorized_role_blocked():
    async def _run():
        # QA Agent trying to call create_file
        req = ToolRequest(
            request_id="sec_req_01",
            tool_name="filesystem.create_file",
            arguments={"file_path": "hacked.py", "content": "bad"},
            authorization_context=ToolAuthorizationContext(
                agent_name="QAAgent",
                role="QA" # QA role is not allowed for create_file
            )
        )
        res = await tool_executor.execute(req)
        assert res.status == ToolExecutionStatusEnum.BLOCKED
        assert "unauthorized" in res.error.lower()

    asyncio.run(_run())

def test_human_approval_required_for_dangerous_tool():
    async def _run():
        # Git commit without approval token
        req = ToolRequest(
            request_id="sec_req_02",
            tool_name="git.commit",
            arguments={"message": "Auto commit"},
            authorization_context=ToolAuthorizationContext(
                agent_name="DeveloperAgent",
                role="DEVELOPER",
                approval_token=None # Missing required human approval token
            )
        )
        res = await tool_executor.execute(req)
        assert res.status in [ToolExecutionStatusEnum.PENDING, ToolExecutionStatusEnum.BLOCKED]
        assert "approval" in res.error.lower()

    asyncio.run(_run())

def test_secret_masker_sanitization():
    raw_token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz1234"
    text = f"Failed to authenticate with token {raw_token} for user."
    masked = SecretMasker.mask_text(text)
    assert raw_token not in masked
    assert "[MASKED_SECRET]" in masked
    
    data = {"api_key": "secret_key_123", "normal": "value"}
    sanitized = SecretMasker.sanitize_dict(data)
    assert sanitized["api_key"] == "[MASKED_SECRET]"
    assert sanitized["normal"] == "value"

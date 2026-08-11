from enum import Enum
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class RiskLevelEnum(str, Enum):
    READ_ONLY = "READ_ONLY"
    LOW_RISK = "LOW_RISK"
    MEDIUM_RISK = "MEDIUM_RISK"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL = "CRITICAL"

class ToolExecutionStatusEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTING = "EXECUTING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"

class ToolCategoryEnum(str, Enum):
    FILESYSTEM = "FILESYSTEM"
    TESTING = "TESTING"
    GIT = "GIT"
    GITHUB = "GITHUB"
    SECURITY = "SECURITY"
    SYSTEM = "SYSTEM"

class ToolAuthorizationContext(BaseModel):
    user_id: str = "user_default_01"
    project_id: str = "proj_default_01"
    agent_name: str = "DeveloperAgent"
    role: str = "DEVELOPER" # PLANNER, ARCHITECT, DEVELOPER, QA, ADMIN, HUMAN_REVIEWER
    workspace_root: Optional[str] = None
    approval_token: Optional[str] = None
    approved_by: Optional[str] = None

class ToolDefinition(BaseModel):
    name: str = Field(..., description="Unique tool identifier e.g. filesystem.read_file")
    description: str = Field(..., description="Human and LLM readable tool description")
    category: ToolCategoryEnum = ToolCategoryEnum.FILESYSTEM
    risk_level: RiskLevelEnum = RiskLevelEnum.READ_ONLY
    requires_approval: bool = False
    allowed_roles: List[str] = Field(default_factory=lambda: ["DEVELOPER", "QA", "ADMIN"])
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for inputs")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON Schema for outputs")

class ToolRequest(BaseModel):
    request_id: str = Field(..., description="Unique idempotency ID for tool invocation")
    tool_name: str = Field(..., description="Target tool name from registry")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Input parameters")
    authorization_context: ToolAuthorizationContext = Field(default_factory=ToolAuthorizationContext)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ToolResult(BaseModel):
    request_id: str
    tool_name: str
    status: ToolExecutionStatusEnum = ToolExecutionStatusEnum.SUCCESS
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    completed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def is_success(self) -> bool:
        return self.status == ToolExecutionStatusEnum.SUCCESS


class AuditLogRecord(BaseModel):
    request_id: str
    user_id: str
    project_id: str
    agent_name: str
    tool_name: str
    risk_level: RiskLevelEnum
    arguments_hash: str
    approval_status: str
    execution_status: str
    started_at: str
    completed_at: str
    duration_ms: float
    error_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

# MCP Standard Schema Objects (Latest Stateless Standard)
class MCPToolInfo(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any]

class MCPListToolsResult(BaseModel):
    tools: List[MCPToolInfo] = Field(default_factory=list)

class MCPCallToolRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    context: Optional[ToolAuthorizationContext] = None

class MCPContentItem(BaseModel):
    type: str = "text"
    text: str

class MCPCallToolResult(BaseModel):
    content: List[MCPContentItem] = Field(default_factory=list)
    isError: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)

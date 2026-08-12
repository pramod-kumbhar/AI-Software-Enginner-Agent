from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class ProviderTypeEnum(str, Enum):
    OLLAMA = "ollama"
    MOCK = "mock"
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    HUGGINGFACE = "huggingface"

class QuotaStatusEnum(str, Enum):
    ALLOWED = "ALLOWED"
    WARNING = "WARNING"
    HIGH_USAGE = "HIGH_USAGE"
    BLOCKED = "BLOCKED"

class AlertTypeEnum(str, Enum):
    TOKEN_THRESHOLD = "TOKEN_THRESHOLD"
    COST_THRESHOLD = "COST_THRESHOLD"
    REQUEST_THRESHOLD = "REQUEST_THRESHOLD"
    AGENT_LOOP_THRESHOLD = "AGENT_LOOP_THRESHOLD"
    TOOL_CALL_THRESHOLD = "TOOL_CALL_THRESHOLD"
    DAILY_LIMIT = "DAILY_LIMIT"
    MONTHLY_LIMIT = "MONTHLY_LIMIT"

class ConfigStatusResponse(BaseModel):
    environment: str
    app_name: str
    debug: bool
    version: str
    configured_providers: List[str]
    database_configured: bool
    redis_configured: bool
    github_configured: bool
    observability_enabled: bool
    security_status: str

class ProviderHealthResponse(BaseModel):
    provider: str
    configured: bool
    available: bool
    model: str
    latency_ms: float = 0.0
    error: Optional[str] = None

class TokenUsageRecord(BaseModel):
    usage_id: str
    user_id: str = "default_user"
    project_id: str = "default_project"
    task_id: str = "default_task"
    agent: str = "DeveloperAgent"
    provider: str = "ollama"
    model: str = "llama3:latest"
    request_id: str = Field(default_factory=lambda: f"req_{int(datetime.now(timezone.utc).timestamp()*1000)}")
    trace_id: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    status: str = "SUCCESS"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ModelPricing(BaseModel):
    provider: str
    model: str
    input_cost_per_1k: float = 0.0
    output_cost_per_1k: float = 0.0
    currency: str = "USD"
    active: bool = True

class CostRecord(BaseModel):
    cost_id: str
    usage_id: str
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    currency: str = "USD"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class QuotaDecision(BaseModel):
    decision: QuotaStatusEnum
    current_value: float
    limit_value: float
    unit: str
    message: str

class UsageSummary(BaseModel):
    total_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    average_latency_ms: float = 0.0
    failed_requests: int = 0
    provider_breakdown: Dict[str, int] = Field(default_factory=dict)
    model_breakdown: Dict[str, int] = Field(default_factory=dict)
    agent_breakdown: Dict[str, int] = Field(default_factory=dict)

class UsageAlert(BaseModel):
    alert_id: str
    user_id: str
    project_id: str
    alert_type: AlertTypeEnum
    threshold: float
    current_value: float
    unit: str
    severity: str
    status: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ConfigAuditFinding(BaseModel):
    rule_id: str
    severity: str
    title: str
    description: str
    remediation: str

class ConfigAuditResult(BaseModel):
    is_compliant: bool
    environment: str
    findings: List[ConfigAuditFinding] = Field(default_factory=list)
    checked_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

from typing import Optional, List
from pydantic import BaseModel, Field

class ApplicationSettings(BaseModel):
    APP_ENV: str = Field(default="development", description="Environment: development, test, staging, production")
    APP_NAME: str = Field(default="ai-software-engineer-agent", description="Application service identifier")
    DEBUG: bool = Field(default=True, description="Debug mode flag")
    PROJECT_NAME: str = Field(default="AI Software Engineer Agent Platform", description="Display project name")
    VERSION: str = Field(default="1.0.0", description="API Version")
    API_V1_STR: str = Field(default="/api/v1", description="API prefix")

class DatabaseSettings(BaseModel):
    DATABASE_URL: Optional[str] = Field(default=None, description="Full PostgreSQL connection string")
    POSTGRES_SERVER: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL user")
    POSTGRES_PASSWORD: str = Field(default="", description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="swe_planner_db", description="Database name")

class RedisSettings(BaseModel):
    REDIS_URL: Optional[str] = Field(default=None, description="Full Redis connection URL")
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")

class LLMSettings(BaseModel):
    LLM_PROVIDER: str = Field(default="ollama", description="Active LLM provider (ollama, mock, groq, openai, anthropic, google, huggingface)")
    LLM_MODEL: str = Field(default="llama3:latest", description="Primary model identifier")
    LLM_API_KEY: Optional[str] = Field(default=None, description="Generic provider API key")
    
    # Ollama Local Configuration (Free Local First)
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434", description="Ollama server URL")
    OLLAMA_MODEL: str = Field(default="llama3:latest", description="Ollama model name")
    OLLAMA_TEMPERATURE: float = Field(default=0.2, ge=0.0, le=2.0)
    OLLAMA_REQUEST_TIMEOUT: float = Field(default=120.0, ge=1.0)
    
    # Optional Cloud Providers
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None

class EmbeddingSettings(BaseModel):
    EMBEDDING_PROVIDER: str = Field(default="local", description="Embedding provider (local, ollama, mock, huggingface)")
    EMBEDDING_MODEL: str = Field(default="all-MiniLM-L6-v2", description="Embedding model name")

class GitHubSettings(BaseModel):
    GITHUB_TOKEN: Optional[str] = Field(default=None, description="GitHub Personal Access Token")
    GITHUB_OWNER: Optional[str] = Field(default=None, description="GitHub user/org name")
    GITHUB_REPOSITORY: Optional[str] = Field(default=None, description="GitHub repository name")
    GITHUB_API_BASE_URL: str = Field(default="https://api.github.com", description="GitHub REST API base")

class SecuritySettings(BaseModel):
    JWT_SECRET: Optional[str] = Field(default=None, description="JWT encryption secret")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1)
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, ge=1)
    REQUIRE_HUMAN_APPROVAL_FOR_HIGH_RISK: bool = Field(default=True)
    ALLOWED_CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

class AgentSettings(BaseModel):
    MAX_PLANNING_RETRIES: int = Field(default=3, ge=1)
    MAX_AGENT_ITERATIONS: int = Field(default=10, ge=1, le=50)
    MAX_REPAIR_ATTEMPTS: int = Field(default=3, ge=1, le=10)
    AUTO_REPAIR_ENABLED: bool = Field(default=True)
    WORKSPACE_BASE_DIR: str = Field(default="generated_projects")
    TOOL_RATE_LIMIT_PER_MINUTE: int = Field(default=120)
    TOOL_TIMEOUT_SECONDS: float = Field(default=30.0)
    TEST_TIMEOUT_SECONDS: float = Field(default=15.0)

class ReleaseSettings(BaseModel):
    RELEASE_MIN_QA_SCORE: float = Field(default=85.0, ge=0.0, le=100.0)
    RELEASE_MIN_COVERAGE: float = Field(default=80.0, ge=0.0, le=100.0)
    RELEASE_MAX_RISK_SCORE: float = Field(default=40.0, ge=0.0, le=100.0)
    RELEASE_REQUIRE_HUMAN_APPROVAL: bool = Field(default=True)

class ObservabilitySettings(BaseModel):
    LOG_LEVEL: str = Field(default="INFO")
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_TRACING: bool = Field(default=False)
    LANGSMITH_PROJECT: str = Field(default="swe-agent-platform")
    SENTRY_DSN: Optional[str] = None

class CostSettings(BaseModel):
    MAX_LLM_TOKENS_PER_REQUEST: int = Field(default=6000, ge=100)
    MAX_PROJECT_TOKENS_PER_DAY: int = Field(default=100000, ge=1000)
    COST_ALERT_THRESHOLD_USD: float = Field(default=1.00, ge=0.0)
    DAILY_COST_LIMIT_USD: float = Field(default=5.00, ge=0.0)
    ENABLE_COST_ALERTS: bool = Field(default=True)

class DeploymentSettings(BaseModel):
    PRODUCTION_DEPLOYMENT_ENABLED: bool = Field(default=False)
    ROLLBACK_ENABLED: bool = Field(default=True)
    HEALTH_CHECK_TIMEOUT: float = Field(default=120.0)
    HEALTH_CHECK_INTERVAL: float = Field(default=10.0)
    MAX_HEALTH_CHECK_ATTEMPTS: int = Field(default=12)
    MAX_DEPLOYMENT_RETRIES: int = Field(default=2)
    DEPLOYMENT_ENVIRONMENT: str = Field(default="staging")
    AWS_REGION: str = Field(default="us-east-1")
    AWS_ROLE_ARN: Optional[str] = None

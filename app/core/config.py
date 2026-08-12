import os
from typing import Optional, List, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from app.core.config_groups import (
    ApplicationSettings,
    DatabaseSettings,
    RedisSettings,
    LLMSettings,
    EmbeddingSettings,
    GitHubSettings,
    SecuritySettings,
    AgentSettings,
    ReleaseSettings,
    ObservabilitySettings,
    CostSettings,
    DeploymentSettings
)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # 1. Application Settings
    APP_ENV: str = Field(default="development")
    APP_NAME: str = Field(default="ai-software-engineer-agent")
    DEBUG: bool = Field(default=True)
    PROJECT_NAME: str = Field(default="AI Software Engineer Agent Platform")
    VERSION: str = Field(default="1.0.0")
    API_V1_STR: str = Field(default="/api/v1")

    # 2. Database Settings
    DATABASE_URL: Optional[str] = None
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "swe_planner_db"

    # 3. Redis Settings
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # 4. LLM Provider Settings (Local First)
    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "llama3:latest"
    LLM_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3:latest"
    OLLAMA_TEMPERATURE: float = 0.2
    OLLAMA_REQUEST_TIMEOUT: float = 120.0
    
    # Optional Cloud Providers
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None

    # 5. Embedding Settings
    EMBEDDING_PROVIDER: str = "local"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # 6. GitHub Integration Settings
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_OWNER: Optional[str] = None
    GITHUB_REPOSITORY: Optional[str] = None
    GITHUB_API_BASE_URL: str = "https://api.github.com"

    # 7. Security & JWT Settings
    JWT_SECRET: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REQUIRE_HUMAN_APPROVAL_FOR_HIGH_RISK: bool = True
    ALLOWED_CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    # 8. Agent Execution Guards
    MAX_PLANNING_RETRIES: int = 3
    MAX_AGENT_ITERATIONS: int = 10
    MAX_REPAIR_ATTEMPTS: int = 3
    AUTO_REPAIR_ENABLED: bool = True
    WORKSPACE_BASE_DIR: str = "generated_projects"
    TOOL_RATE_LIMIT_PER_MINUTE: int = 120
    TOOL_TIMEOUT_SECONDS: float = 30.0
    TEST_TIMEOUT_SECONDS: float = 15.0

    # 9. Release Governance & Quality Thresholds
    RELEASE_MIN_QA_SCORE: float = 85.0
    RELEASE_MIN_COVERAGE: float = 80.0
    RELEASE_MAX_RISK_SCORE: float = 40.0
    RELEASE_REQUIRE_HUMAN_APPROVAL: bool = True

    # 10. Observability Settings
    LOG_LEVEL: str = "INFO"
    LANGSMITH_API_KEY: Optional[str] = None
    LANGSMITH_TRACING: bool = False
    LANGSMITH_PROJECT: str = "swe-agent-platform"
    SENTRY_DSN: Optional[str] = None

    # 11. Cost & Token Limits (FinOps)
    MAX_LLM_TOKENS_PER_REQUEST: int = 6000
    MAX_PROJECT_TOKENS_PER_DAY: int = 100000
    COST_ALERT_THRESHOLD_USD: float = 1.00
    DAILY_COST_LIMIT_USD: float = 5.00
    ENABLE_COST_ALERTS: bool = True

    # 12. Deployment Settings
    PRODUCTION_DEPLOYMENT_ENABLED: bool = True
    ROLLBACK_ENABLED: bool = True
    HEALTH_CHECK_TIMEOUT: float = 120.0
    HEALTH_CHECK_INTERVAL: float = 10.0
    HEALTH_CHECK_TIMEOUT_SECONDS: float = 10.0
    HEALTH_CHECK_INTERVAL_SECONDS: float = 2.0
    MAX_HEALTH_CHECK_ATTEMPTS: int = 12
    MAX_DEPLOYMENT_RETRIES: int = 2
    DEPLOYMENT_ENVIRONMENT: str = "staging"
    AWS_REGION: str = "us-east-1"
    AWS_ROLE_ARN: Optional[str] = None

    # Backward compatibility properties
    CI_POLL_INTERVAL_SECONDS: float = 5.0
    CI_MAX_POLL_ATTEMPTS: int = 30
    CI_MAX_REPAIR_ATTEMPTS: int = 3
    CI_LOG_MAX_CHARS: int = 20000

    @property
    def postgres_dsn(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"

    @property
    def is_test(self) -> bool:
        return self.APP_ENV.lower() == "test" or "PYTEST_CURRENT_TEST" in os.environ

    @property
    def is_development(self) -> bool:
        return self.APP_ENV.lower() == "development"

    def get_safe_status(self) -> Dict[str, Any]:
        """Returns non-sensitive configuration status for APIs and health checks."""
        return {
            "environment": self.APP_ENV,
            "app_name": self.APP_NAME,
            "debug": self.DEBUG,
            "version": self.VERSION,
            "primary_provider": self.LLM_PROVIDER,
            "primary_model": self.LLM_MODEL,
            "database_configured": bool(self.DATABASE_URL or self.POSTGRES_SERVER),
            "redis_configured": bool(self.REDIS_URL or self.REDIS_HOST),
            "github_configured": bool(self.GITHUB_TOKEN),
            "observability_enabled": bool(self.LANGSMITH_TRACING),
            "production_deployment_enabled": self.PRODUCTION_DEPLOYMENT_ENABLED,
            "rollback_enabled": self.ROLLBACK_ENABLED,
            "max_tokens_per_request": self.MAX_LLM_TOKENS_PER_REQUEST,
            "daily_cost_limit_usd": self.DAILY_COST_LIMIT_USD
        }

settings = Settings()

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env", extra="ignore")

    PROJECT_NAME: str = "AI Software Engineer Agent - Planner Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3:latest"
    OLLAMA_TEMPERATURE: float = 0.2
    OLLAMA_REQUEST_TIMEOUT: float = 120.0
    
    # Storage & Persistence
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "swe_planner_db"
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # Execution Guards
    MAX_PLANNING_RETRIES: int = 3
    LOG_LEVEL: str = "INFO"

    # Tool & MCP Configuration
    WORKSPACE_BASE_DIR: str = "generated_projects"
    TOOL_RATE_LIMIT_PER_MINUTE: int = 120
    TOOL_TIMEOUT_SECONDS: float = 30.0
    TEST_TIMEOUT_SECONDS: float = 15.0
    REQUIRE_HUMAN_APPROVAL_FOR_HIGH_RISK: bool = True

    # GitHub Integration Configuration
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_OWNER: Optional[str] = None
    GITHUB_REPOSITORY: Optional[str] = None
    GITHUB_API_BASE_URL: str = "https://api.github.com"

    # Day 11 CI/CD Monitoring & Autonomous Repair Configuration
    CI_POLL_INTERVAL_SECONDS: float = 5.0
    CI_MAX_POLL_ATTEMPTS: int = 30
    CI_MAX_REPAIR_ATTEMPTS: int = 3
    CI_LOG_MAX_CHARS: int = 20000
    AUTO_REPAIR_ENABLED: bool = True

    # Day 12 Release Governance, Deployment, Observability & Rollback Configuration
    RELEASE_MIN_QA_SCORE: float = 80.0
    RELEASE_MIN_COVERAGE: float = 75.0
    RELEASE_MAX_RISK_SCORE: float = 65.0
    RELEASE_REQUIRE_HUMAN_APPROVAL: bool = True
    PRODUCTION_DEPLOYMENT_ENABLED: bool = True
    ROLLBACK_ENABLED: bool = True
    HEALTH_CHECK_TIMEOUT_SECONDS: float = 10.0
    HEALTH_CHECK_INTERVAL_SECONDS: float = 2.0
    MAX_HEALTH_CHECK_ATTEMPTS: int = 12
    MAX_DEPLOYMENT_RETRIES: int = 2
    DEPLOYMENT_ENVIRONMENT: str = "staging"

    @property
    def postgres_dsn(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()


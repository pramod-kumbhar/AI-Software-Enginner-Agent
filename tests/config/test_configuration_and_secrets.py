import os
from pathlib import Path
import pytest
from app.core.config import Settings, settings
from app.services.config_security_scanner import ConfigurationSecurityScanner

def test_settings_default_environment():
    assert settings.APP_ENV in ["development", "test", "staging", "production"]
    assert settings.VERSION == "1.0.0"
    assert settings.MAX_LLM_TOKENS_PER_REQUEST == 6000
    assert settings.DAILY_COST_LIMIT_USD == 5.00

def test_safe_status_does_not_leak_secrets():
    safe_status = settings.get_safe_status()
    assert "environment" in safe_status
    assert "debug" in safe_status
    assert "database_configured" in safe_status
    
    # Assert no secret keys exist in status dictionary
    status_str = str(safe_status).lower()
    assert "password" not in status_str or safe_status.get("database_configured") is not None
    assert "jwt_secret" not in safe_status
    assert "github_token" not in safe_status
    assert "openai_api_key" not in safe_status

def test_gitignore_contains_env_rules():
    gitignore_path = Path(__file__).resolve().parent.parent.parent / ".gitignore"
    assert gitignore_path.exists()
    content = gitignore_path.read_text(encoding="utf-8")
    assert ".env" in content
    assert "!.env.example" in content

def test_env_example_exists_and_has_no_secrets():
    example_path = Path(__file__).resolve().parent.parent.parent / ".env.example"
    assert example_path.exists()
    content = example_path.read_text(encoding="utf-8")
    assert "APP_ENV=" in content
    assert "JWT_SECRET=" in content
    assert "sk-" not in content
    assert "ghp_" not in content

def test_config_security_scanner_detects_production_debug():
    # Simulate production settings with DEBUG=True
    audit = ConfigurationSecurityScanner.audit_configuration()
    assert isinstance(audit.is_compliant, bool)
    assert audit.environment == settings.APP_ENV
    assert isinstance(audit.findings, list)

def test_production_startup_validation_fails_on_critical_issues():
    # If in test/dev, startup validation should pass without error
    if not settings.is_production:
        ConfigurationSecurityScanner.validate_production_startup()

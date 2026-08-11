import pytest
from app.core.secret_scanner import secret_scanner
from app.schemas.security import SecuritySeverityEnum

def test_detect_github_token():
    raw_code = 'GITHUB_TOKEN = "ghp_1234567890abcdef1234567890abcdef1234"'
    findings = secret_scanner.scan_text(raw_code, file_path="app/config.py")
    assert len(findings) == 1
    assert findings[0].severity == SecuritySeverityEnum.CRITICAL
    assert "GitHub Personal Access Token" in findings[0].title
    assert "ghp_****" in findings[0].evidence

def test_detect_aws_access_key():
    raw_code = 'AWS_KEY = "AKIA1234567890ABCDEF"'
    findings = secret_scanner.scan_text(raw_code, file_path="deploy/aws.py")
    assert len(findings) == 1
    assert findings[0].severity == SecuritySeverityEnum.CRITICAL
    assert "AKIA****" in findings[0].evidence

def test_detect_database_url_with_credentials():
    raw_code = 'DATABASE_URL = "postgresql://dbuser:SuperSecretPass123@db.prod.internal:5432/appdb"'
    findings = secret_scanner.scan_text(raw_code, file_path="app/db.py")
    assert len(findings) >= 1
    assert any("Database Connection" in f.title for f in findings)

def test_secret_masking_scrubs_sensitive_data():
    raw_text = "Deploying with ghp_1234567890abcdef1234567890abcdef1234 and AKIA1234567890ABCDEF"
    masked = secret_scanner.mask_secret(raw_text)
    assert "ghp_1234567890abcdef1234567890abcdef1234" not in masked
    assert "AKIA1234567890ABCDEF" not in masked
    assert "ghp_****" in masked
    assert "AKIA****" in masked

import pytest
from app.services.security_gate import security_gate
from app.services.security_repair import security_repair_engine
from app.services.filesystem import FilesystemService
from app.schemas.security import (
    SecurityFinding,
    SecuritySeverityEnum,
    SecurityCategoryEnum,
    SecurityStatusEnum,
    SecurityDecisionEnum
)

def test_security_gate_critical_issue_blocks():
    findings = [
        SecurityFinding(
            finding_id="f1",
            category=SecurityCategoryEnum.SECRETS,
            severity=SecuritySeverityEnum.CRITICAL,
            title="Exposed AWS Key",
            description="Hardcoded AKIA key",
            impact="Data exfiltration",
            recommendation="Mask key",
            auto_fixable=True
        )
    ]
    score, status, decision, blockers = security_gate.evaluate(findings)
    assert score == 75.0
    assert status == SecurityStatusEnum.CRITICAL_SECURITY_BLOCK
    assert decision == SecurityDecisionEnum.CRITICAL_BLOCK
    assert len(blockers) == 1

def test_security_auto_repair_secret_masking(tmp_path):
    fs = FilesystemService(workspace_root=str(tmp_path))
    fs.write_file("app/config.py", 'API_KEY = "ghp_1234567890abcdef1234567890abcdef1234"')
    
    finding = SecurityFinding(
        finding_id="f_sec_01",
        category=SecurityCategoryEnum.SECRETS,
        severity=SecuritySeverityEnum.HIGH,
        title="Hardcoded API Key",
        description="Found API_KEY assignment",
        file_path="app/config.py",
        impact="Credential theft",
        recommendation="Use os.getenv",
        auto_fixable=True
    )
    
    plan = security_repair_engine.create_repair_plan(finding, attempt_number=1)
    ok, msg = security_repair_engine.execute_auto_repair(plan, finding, fs)
    assert ok is True
    
    # Verify file was updated to os.getenv
    _, repaired_content = fs.read_file("app/config.py")
    assert "os.getenv" in repaired_content
    assert "ghp_1234567890abcdef1234567890abcdef1234" not in repaired_content

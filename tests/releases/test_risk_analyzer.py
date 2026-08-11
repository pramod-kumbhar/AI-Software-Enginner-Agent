from app.schemas.release import RiskLevelEnum, ChangeCategoryEnum
from app.services.risk_analyzer import risk_analyzer

def test_documentation_only_low_risk():
    files = ["README.md", "docs/architecture.md"]
    score, level, cats, notes = risk_analyzer.analyze_risk(changed_files=files)
    assert level == RiskLevelEnum.LOW
    assert score <= 20.0
    assert ChangeCategoryEnum.DOCUMENTATION in cats

def test_auth_changes_high_risk():
    files = ["app/core/auth.py", "app/api/v1/jwt_auth.py"]
    score, level, cats, notes = risk_analyzer.analyze_risk(changed_files=files)
    assert level in [RiskLevelEnum.HIGH, RiskLevelEnum.CRITICAL]
    assert score >= 40.0
    assert ChangeCategoryEnum.AUTHENTICATION in cats

def test_payment_changes_critical_risk():
    files = ["app/services/payment_gateway.py", "app/models/wallet_transaction.py"]
    score, level, cats, notes = risk_analyzer.analyze_risk(changed_files=files)
    assert level in [RiskLevelEnum.HIGH, RiskLevelEnum.CRITICAL]
    assert ChangeCategoryEnum.PAYMENT in cats

def test_destructive_db_migration_detection():
    files = ["alembic/versions/002_migration.py"]
    diff = "op.execute('DROP TABLE customer_accounts CASCADE')"
    score, level, cats, notes = risk_analyzer.analyze_risk(changed_files=files, diff_text=diff)
    assert level in [RiskLevelEnum.HIGH, RiskLevelEnum.CRITICAL]
    assert any("DESTRUCTIVE SQL" in n for n in notes)

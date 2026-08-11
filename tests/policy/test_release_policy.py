import pytest
from app.schemas.release import (
    ReleaseReadiness,
    ReleaseDecisionEnum,
    EnvironmentEnum,
    HealthStateEnum
)
from app.services.policy_engine import policy_engine

def test_valid_release_policy_staging():
    readiness = ReleaseReadiness(
        release_id="rel_val_01",
        version="1.0.0",
        project_id="proj_01",
        commit_sha="c0ffee1",
        branch="main",
        ci_status="PASS",
        qa_status="PASS",
        qa_score=95.0,
        security_status="PASS",
        architecture_status="PASS"
    )
    decision, blockers, warnings = policy_engine.evaluate(readiness, EnvironmentEnum.STAGING)
    assert decision in [ReleaseDecisionEnum.DEPLOY, ReleaseDecisionEnum.DEPLOY_WITH_APPROVAL]
    assert len(blockers) == 0


def test_low_qa_score_blocks_release():
    readiness = ReleaseReadiness(
        release_id="rel_val_02",
        version="1.0.0",
        project_id="proj_01",
        commit_sha="c0ffee1",
        branch="main",
        ci_status="PASS",
        qa_status="FAILED",
        qa_score=65.0, # Below 80.0
        security_status="PASS",
        architecture_status="PASS"
    )
    decision, blockers, warnings = policy_engine.evaluate(readiness, EnvironmentEnum.STAGING)
    assert decision == ReleaseDecisionEnum.BLOCK
    assert any("QA validation" in b for b in blockers)

def test_ci_failure_blocks_release():
    readiness = ReleaseReadiness(
        release_id="rel_val_03",
        version="1.0.0",
        project_id="proj_01",
        commit_sha="c0ffee1",
        branch="main",
        ci_status="FAILED",
        qa_status="PASS",
        qa_score=90.0,
        security_status="PASS",
        architecture_status="PASS"
    )
    decision, blockers, warnings = policy_engine.evaluate(readiness, EnvironmentEnum.STAGING)
    assert decision == ReleaseDecisionEnum.BLOCK
    assert any("CI pipeline" in b for b in blockers)

def test_security_failure_blocks_release():
    readiness = ReleaseReadiness(
        release_id="rel_val_04",
        version="1.0.0",
        project_id="proj_01",
        commit_sha="c0ffee1",
        branch="main",
        ci_status="PASS",
        qa_status="PASS",
        qa_score=90.0,
        security_status="FAILED",
        architecture_status="PASS"
    )
    decision, blockers, warnings = policy_engine.evaluate(readiness, EnvironmentEnum.STAGING)
    assert decision == ReleaseDecisionEnum.BLOCK
    assert any("Security" in b for b in blockers)

def test_production_deployment_requires_approval():
    readiness = ReleaseReadiness(
        release_id="rel_val_05",
        version="1.0.0",
        project_id="proj_01",
        commit_sha="c0ffee1",
        branch="main",
        ci_status="PASS",
        qa_status="PASS",
        qa_score=95.0,
        security_status="PASS",
        architecture_status="PASS"
    )
    decision, blockers, warnings = policy_engine.evaluate(readiness, EnvironmentEnum.PRODUCTION)
    assert decision == ReleaseDecisionEnum.DEPLOY_WITH_APPROVAL
    assert len(blockers) == 0

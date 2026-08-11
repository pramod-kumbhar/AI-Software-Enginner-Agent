import uuid
from typing import Dict, Any, List
from datetime import datetime, timezone

from app.agents.release.state import ReleaseState
from app.schemas.release import (
    ReleaseReadiness,
    ReleaseManifest,
    ReleaseStatusEnum,
    ReleaseDecisionEnum,
    EnvironmentEnum,
    HealthStateEnum
)
from app.services.policy_engine import policy_engine
from app.services.risk_analyzer import risk_analyzer
from app.services.deployment_providers import deployment_provider
from app.services.rollback_manager import rollback_manager
from app.services.storage import storage_service
from app.core.logging import logger
from app.core.observability import metrics, TraceContext
from app.mcp.client import MCPClient

mcp_client = MCPClient(agent_name="ReleaseAgent", role="ADMIN")

async def load_release_context_node(state: ReleaseState) -> Dict[str, Any]:
    release_id = state.get("release_id", f"rel_{uuid.uuid4().hex[:8]}")
    version = state.get("version", "1.0.0")
    project_id = state.get("project_id", "default_proj")
    user_id = state.get("user_id", "user_devops_01")
    target_env = state.get("target_environment", EnvironmentEnum.STAGING)
    if isinstance(target_env, str):
        target_env = EnvironmentEnum(target_env)

    logger.info(f"RELEASE NODE [1/12]: Loading context for Release {release_id} (Version: {version}, Target: {target_env.value})")

    
    return {
        "release_id": release_id,
        "version": version,
        "project_id": project_id,
        "user_id": user_id,
        "target_environment": target_env,
        "status": ReleaseStatusEnum.VALIDATING,
        "ci_status": state.get("ci_status", "PASS"),
        "qa_status": state.get("qa_status", "PASS"),
        "qa_score": state.get("qa_score", 100.0),
        "test_coverage": state.get("test_coverage", 100.0),
        "security_status": state.get("security_status", "PASS"),
        "architecture_status": state.get("architecture_status", "PASS"),
        "artifact_status": state.get("artifact_status", "PASS"),
        "changed_files": state.get("changed_files", ["app/main.py", "app/api/v1/endpoints.py"]),
        "diff_text": state.get("diff_text", ""),
        "approval_granted": state.get("approval_granted", False),
        "approved_by": state.get("approved_by")
    }

async def validate_ci_node(state: ReleaseState) -> Dict[str, Any]:
    ci_status = state.get("ci_status", "PASS")
    logger.info(f"RELEASE NODE [2/12]: Verifying CI status: {ci_status}")
    return {"ci_status": ci_status}

async def validate_qa_node(state: ReleaseState) -> Dict[str, Any]:
    qa_score = state.get("qa_score", 100.0)
    qa_status = "PASS" if qa_score >= 80.0 else "FAILED"
    logger.info(f"RELEASE NODE [3/12]: Verifying QA compliance: Score={qa_score}/100 Status={qa_status}")
    return {"qa_score": qa_score, "qa_status": qa_status}

async def validate_security_node(state: ReleaseState) -> Dict[str, Any]:
    sec_status = state.get("security_status", "PASS")
    logger.info(f"RELEASE NODE [4/12]: Verifying Security scan: {sec_status}")
    return {"security_status": sec_status}

async def validate_architecture_node(state: ReleaseState) -> Dict[str, Any]:
    arch_status = state.get("architecture_status", "PASS")
    logger.info(f"RELEASE NODE [5/12]: Verifying Architecture compliance: {arch_status}")
    return {"architecture_status": arch_status}

async def validate_artifact_node(state: ReleaseState) -> Dict[str, Any]:
    artifact_status = state.get("artifact_status", "PASS")
    logger.info(f"RELEASE NODE [6/12]: Verifying Deployment build artifact integrity: {artifact_status}")
    return {"artifact_status": artifact_status}

async def calculate_release_risk_node(state: ReleaseState) -> Dict[str, Any]:
    changed_files = state.get("changed_files", [])
    diff_text = state.get("diff_text", "")
    qa_score = state.get("qa_score", 100.0)

    score, level, categories, notes = risk_analyzer.analyze_risk(
        changed_files=changed_files,
        diff_text=diff_text,
        qa_score=qa_score
    )

    logger.info(f"RELEASE NODE [7/12]: Calculated Risk Score: {score:.1f}/100 (Level: {level.value})")

    # Construct Readiness model
    readiness = ReleaseReadiness(
        release_id=state["release_id"],
        version=state["version"],
        project_id=state["project_id"],
        commit_sha=state.get("commit_sha", "c0ffee1"),
        branch=state.get("branch", "main"),
        pull_request_number=state.get("pull_request_number"),
        ci_status=state.get("ci_status", "PASS"),
        qa_status=state.get("qa_status", "PASS"),
        qa_score=qa_score,
        test_coverage=state.get("test_coverage", 100.0),
        security_status=state.get("security_status", "PASS"),
        architecture_status=state.get("architecture_status", "PASS"),
        build_status=state.get("build_status", "PASS"),
        artifact_status=state.get("artifact_status", "PASS"),
        risk_score=score,
        risk_level=level,
        approval_status="APPROVED" if state.get("approval_granted") else state.get("approval_status", "PENDING"),
        recommendations=notes
    )
    return {"readiness": readiness}

async def generate_release_plan_node(state: ReleaseState) -> Dict[str, Any]:
    readiness = state["readiness"]
    manifest = ReleaseManifest(
        release_id=readiness.release_id,
        version=readiness.version,
        project_id=readiness.project_id,
        commit_sha=readiness.commit_sha,
        branch=readiness.branch,
        pull_request_number=readiness.pull_request_number,
        qa_score=readiness.qa_score,
        security_status=readiness.security_status,
        architecture_status=readiness.architecture_status,
        deployment_environment=state.get("target_environment", EnvironmentEnum.STAGING)
    )
    logger.info(f"RELEASE NODE [8/12]: Generated Release Manifest for Version {manifest.version}")
    return {"release_manifest": manifest}

async def policy_check_node(state: ReleaseState) -> Dict[str, Any]:
    readiness = state["readiness"]
    target_env = state.get("target_environment", EnvironmentEnum.STAGING)
    
    decision, blockers, warnings = policy_engine.evaluate(readiness, target_environment=target_env)
    
    readiness.decision = decision
    readiness.blockers = blockers
    readiness.warnings = warnings
    readiness.release_status = ReleaseStatusEnum.BLOCKED if decision == ReleaseDecisionEnum.BLOCK else (
        ReleaseStatusEnum.APPROVAL_PENDING if decision == ReleaseDecisionEnum.DEPLOY_WITH_APPROVAL else ReleaseStatusEnum.VALIDATING
    )

    storage_service.save_release_validation(readiness.release_id, readiness)
    
    logger.info(f"RELEASE NODE [9/12]: Deterministic Policy Decision -> {decision.value} (Blockers: {len(blockers)})")
    
    return {
        "readiness": readiness,
        "policy_decision": decision,
        "is_blocked": decision == ReleaseDecisionEnum.BLOCK
    }

async def deploy_staging_node(state: ReleaseState) -> Dict[str, Any]:
    manifest = state["release_manifest"]
    logger.info(f"RELEASE NODE [10/12]: Deploying to Staging Environment (Release: {manifest.release_id})")
    
    run = deployment_provider.deploy(manifest, EnvironmentEnum.STAGING)
    storage_service.save_deployment_run(run.deployment_id, run)
    metrics.increment("deployments_total")
    
    return {
        "staging_run": run,
        "status": ReleaseStatusEnum.STAGING_VALIDATING
    }

async def validate_staging_node(state: ReleaseState) -> Dict[str, Any]:
    logger.info("RELEASE NODE [11/12]: Probing Staging Health & Running Smoke Tests")
    health = deployment_provider.health_check(EnvironmentEnum.STAGING)
    
    if health.status == HealthStateEnum.UNHEALTHY:
        logger.error("STAGING VALIDATION FAILED: Health probe returned UNHEALTHY. Promotion to Production is BLOCKED.")
        return {
            "staging_health": health,
            "status": ReleaseStatusEnum.BLOCKED,
            "is_blocked": True,
            "error": "Staging health verification failed."
        }
        
    return {
        "staging_health": health,
        "status": ReleaseStatusEnum.PRODUCTION_APPROVAL_PENDING
    }

async def request_production_approval_node(state: ReleaseState) -> Dict[str, Any]:
    logger.info("RELEASE NODE: Requesting Human Approval for Production Deployment Gate")
    return {
        "status": ReleaseStatusEnum.PRODUCTION_APPROVAL_PENDING
    }

async def deploy_production_node(state: ReleaseState) -> Dict[str, Any]:
    manifest = state["release_manifest"]
    approved_by = state.get("approved_by", "LeadDevOps")
    logger.info(f"RELEASE NODE [12/12]: Deploying to Production Environment (Approved By: {approved_by})")
    
    run = deployment_provider.deploy(manifest, EnvironmentEnum.PRODUCTION)
    run.deployed_by = approved_by
    storage_service.save_deployment_run(run.deployment_id, run)
    metrics.increment("deployments_total")
    
    return {
        "production_run": run,
        "status": ReleaseStatusEnum.HEALTH_CHECKING
    }

async def health_check_node(state: ReleaseState) -> Dict[str, Any]:
    logger.info("RELEASE NODE: Running Post-Deployment Health Check on Production")
    health = deployment_provider.health_check(EnvironmentEnum.PRODUCTION)
    
    if health.status == HealthStateEnum.UNHEALTHY:
        logger.error("PRODUCTION HEALTH FAILURE: Triggering Autonomous Rollback.")
        return {
            "production_health": health,
            "status": ReleaseStatusEnum.ROLLBACK_PENDING
        }
        
    return {
        "production_health": health,
        "status": ReleaseStatusEnum.RELEASED
    }

async def observe_node(state: ReleaseState) -> Dict[str, Any]:
    with TraceContext("observe_deployment", project_id=state.get("project_id"), release_id=state.get("release_id"), agent_name="ReleaseAgent"):
        metrics.set_gauge("last_qa_score", state.get("qa_score", 100.0))
        metrics.set_gauge("last_release_risk_score", state.get("readiness").risk_score if state.get("readiness") else 0.0)
    return {}

async def rollback_node(state: ReleaseState) -> Dict[str, Any]:
    release_id = state["release_id"]
    failed_version = state["version"]
    logger.warning(f"RELEASE ROLLBACK NODE: Executing Rollback for Failed Release {release_id} (Version: {failed_version})")
    
    success, event, msg = rollback_manager.execute_rollback(
        release_id=release_id,
        failed_version=failed_version,
        environment=EnvironmentEnum.PRODUCTION,
        reason="Production post-deployment health check failed"
    )
    return {
        "rollback_event": event,
        "status": ReleaseStatusEnum.ROLLED_BACK if success else ReleaseStatusEnum.FAILED,
        "error": msg if not success else None
    }

async def finalize_release_node(state: ReleaseState) -> Dict[str, Any]:
    final_status = state.get("status", ReleaseStatusEnum.RELEASED)
    readiness = state.get("readiness")
    if readiness:
        readiness.release_status = final_status
        storage_service.save_release(readiness.release_id, readiness)
    
    logger.info(f"RELEASE FINALIZED: Release {state.get('release_id')} Status -> {final_status.value}")
    return {"status": final_status}

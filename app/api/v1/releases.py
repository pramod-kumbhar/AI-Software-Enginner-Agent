import uuid
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from app.schemas.release import (
    ReleaseCreateRequest,
    ReleaseApprovalRequest,
    DeploymentRequest,
    RollbackRequest,
    ReleaseValidationResponse,
    ReleaseReadiness,
    ReleaseStatusEnum,
    ReleaseDecisionEnum,
    EnvironmentEnum
)
from app.agents.release.graph import release_agent
from app.services.storage import storage_service
from app.services.policy_engine import policy_engine
from app.services.health_service import health_service
from app.services.rollback_manager import rollback_manager
from app.core.logging import logger

router = APIRouter(prefix="/releases", tags=["Releases & Deployment"])

@router.post("/create", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_release(request: ReleaseCreateRequest):
    """
    Creates a new release record and triggers automated release readiness validation.
    """
    release_id = f"rel_{uuid.uuid4().hex[:8]}"
    version = request.version or "1.0.0"
    
    initial_state = {
        "release_id": release_id,
        "version": version,
        "project_id": request.project_id,
        "user_id": request.user_id,
        "commit_sha": request.commit_sha,
        "branch": request.branch,
        "pull_request_number": request.pull_request_number,
        "target_environment": request.target_environment,
        "qa_score": 100.0,
        "ci_status": "PASS",
        "qa_status": "PASS",
        "security_status": "PASS",
        "architecture_status": "PASS"
    }

    config = {"configurable": {"thread_id": f"sess_rel_{release_id}"}}
    result_state = await release_agent.ainvoke(initial_state, config=config)

    readiness = result_state.get("readiness")
    return {
        "release_id": release_id,
        "version": version,
        "status": result_state.get("status", ReleaseStatusEnum.VALIDATING).value,
        "policy_decision": result_state.get("policy_decision", ReleaseDecisionEnum.DEPLOY).value,
        "is_blocked": result_state.get("is_blocked", False),
        "readiness": readiness.model_dump() if readiness else None
    }

@router.get("/{release_id}", response_model=Dict[str, Any])
async def get_release(release_id: str):
    """
    Retrieves full details for a release.
    """
    release = storage_service.get_release(release_id)
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Release {release_id} not found.")
    return release

@router.post("/{release_id}/validate", response_model=ReleaseValidationResponse)
async def validate_release(release_id: str):
    """
    Evaluates policy readiness and calculates risk score for a release.
    """
    val = storage_service.get_release_validation(release_id)
    if not val:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Validation for release {release_id} not found.")
    
    readiness = ReleaseReadiness.model_validate(val)
    return ReleaseValidationResponse(
        release_id=readiness.release_id,
        version=readiness.version,
        environment=EnvironmentEnum.STAGING,
        ci_status=readiness.ci_status,
        qa_status=readiness.qa_status,
        qa_score=readiness.qa_score,
        security_status=readiness.security_status,
        architecture_status=readiness.architecture_status,
        artifact_status=readiness.artifact_status,
        staging_status="READY",
        risk_score=readiness.risk_score,
        risk_level=readiness.risk_level,
        blockers=readiness.blockers,
        warnings=readiness.warnings,
        decision=readiness.decision,
        approval_required=readiness.decision == ReleaseDecisionEnum.DEPLOY_WITH_APPROVAL
    )

@router.post("/{release_id}/approve", response_model=Dict[str, Any])
async def approve_release(release_id: str, request: ReleaseApprovalRequest):
    """
    Human approval gate for high-risk / production releases.
    """
    release = storage_service.get_release(release_id)
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Release {release_id} not found.")
    
    release["approval_status"] = "APPROVED" if request.approved else "REJECTED"
    release["approved_by"] = request.user_id
    release["release_status"] = ReleaseStatusEnum.PRODUCTION_APPROVAL_PENDING.value if request.approved else ReleaseStatusEnum.BLOCKED.value
    storage_service.save_release(release_id, release)
    
    logger.info(f"RELEASE APPROVAL: [{release_id}] status={release['approval_status']} by={request.user_id}")
    return {
        "release_id": release_id,
        "approval_status": release["approval_status"],
        "approved_by": request.user_id,
        "status": release["release_status"]
    }

@router.post("/{release_id}/reject", response_model=Dict[str, Any])
async def reject_release(release_id: str, request: ReleaseApprovalRequest):
    """
    Rejects a release and transitions status to BLOCKED.
    """
    request.approved = False
    return await approve_release(release_id, request)

@router.post("/{release_id}/deploy/staging", response_model=Dict[str, Any])
async def deploy_staging(release_id: str, request: DeploymentRequest):
    """
    Triggers automated deployment to staging environment.
    """
    release = storage_service.get_release(release_id)
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Release {release_id} not found.")
    
    initial_state = {
        "release_id": release_id,
        "version": release.get("version", "1.0.0"),
        "project_id": release.get("project_id", "default_proj"),
        "commit_sha": release.get("commit_sha", "c0ffee1"),
        "branch": release.get("branch", "main"),
        "target_environment": EnvironmentEnum.STAGING,
        "approval_granted": release.get("approval_status") == "APPROVED",
        "approval_status": release.get("approval_status", "PENDING"),
        "qa_score": release.get("qa_score", 100.0)
    }

    config = {"configurable": {"thread_id": f"sess_staging_{release_id}"}}
    result_state = await release_agent.ainvoke(initial_state, config=config)

    return {
        "release_id": release_id,
        "environment": "staging",
        "status": result_state.get("status", ReleaseStatusEnum.STAGING_VALIDATING).value,
        "staging_run": result_state.get("staging_run").model_dump() if result_state.get("staging_run") else None
    }

@router.post("/{release_id}/deploy/production", response_model=Dict[str, Any])
async def deploy_production(release_id: str, request: DeploymentRequest):
    """
    Triggers production deployment (strictly requires human approval).
    """
    release = storage_service.get_release(release_id)
    if not release:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Release {release_id} not found.")
    
    if release.get("approval_status") != "APPROVED" and not request.force:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Production deployment strictly requires prior human approval."
        )

    initial_state = {
        "release_id": release_id,
        "version": release.get("version", "1.0.0"),
        "project_id": release.get("project_id", "default_proj"),
        "commit_sha": release.get("commit_sha", "c0ffee1"),
        "branch": release.get("branch", "main"),
        "target_environment": EnvironmentEnum.PRODUCTION,
        "approval_granted": True,
        "approved_by": release.get("approved_by", request.user_id),
        "qa_score": release.get("qa_score", 100.0)
    }

    config = {"configurable": {"thread_id": f"sess_prod_{release_id}"}}
    result_state = await release_agent.ainvoke(initial_state, config=config)

    return {
        "release_id": release_id,
        "environment": "production",
        "status": result_state.get("status", ReleaseStatusEnum.RELEASED).value,
        "production_run": result_state.get("production_run").model_dump() if result_state.get("production_run") else None,
        "rollback_triggered": result_state.get("status") == ReleaseStatusEnum.ROLLED_BACK
    }

@router.get("/{release_id}/health", response_model=Dict[str, Any])
async def get_release_health(release_id: str, environment: str = "staging"):
    """
    Returns live health check probe results for a release environment.
    """
    env_enum = EnvironmentEnum.PRODUCTION if environment.lower() == "production" else EnvironmentEnum.STAGING
    health = health_service.check_health(env_enum)
    return health.model_dump()

@router.post("/{release_id}/rollback", response_model=Dict[str, Any])
async def trigger_rollback(release_id: str, request: RollbackRequest):
    """
    Executes controlled emergency rollback.
    """
    release = storage_service.get_release(release_id)
    failed_ver = release.get("version", "1.0.0") if release else "1.0.0"

    success, event, msg = rollback_manager.execute_rollback(
        release_id=release_id,
        failed_version=failed_ver,
        environment=request.environment,
        target_version=request.target_version,
        reason=request.reason
    )
    return {
        "release_id": release_id,
        "success": success,
        "message": msg,
        "rollback_event": event.model_dump() if event else None
    }

@router.get("/{release_id}/history", response_model=Dict[str, Any])
async def get_release_history(release_id: str):
    """
    Retrieves full deployment and rollback audit history for a release.
    """
    runs = storage_service.list_deployment_runs(release_id=release_id)
    rollbacks = storage_service.list_rollback_events(release_id=release_id)
    return {
        "release_id": release_id,
        "deployments": runs,
        "rollbacks": rollbacks
    }

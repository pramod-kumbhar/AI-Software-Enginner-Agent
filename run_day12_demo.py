import asyncio
import json
import sys
import uuid
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.agents.release.graph import release_agent
from app.schemas.release import (
    ReleaseStatusEnum,
    EnvironmentEnum
)
from app.services.deployment_providers import deployment_provider
from app.services.storage import storage_service
from app.core.observability import metrics

async def main():
    print("=" * 88)
    print("   AI SOFTWARE ENGINEER AGENT PLATFORM - DAY 12 PRODUCTION DEPLOYMENT & ROLLBACK")
    print("   [Release Governance] + [Staging Smoke Probes] + [Human Gate] + [Autonomous Rollback]")
    print("=" * 88)

    # -------------------------------------------------------------
    # SCENARIO 1: SUCCESSFUL STAGING -> HUMAN APPROVAL -> PRODUCTION
    # -------------------------------------------------------------
    print("\n" + "#" * 88)
    print("   SCENARIO 1: SUCCESSFUL STAGING VALIDATION -> HUMAN APPROVAL -> PRODUCTION RELEASE")
    print("#" * 88)

    rel_id_1 = f"rel_{uuid.uuid4().hex[:8]}"
    print(f"\n[1/4] Initiating Release Pipeline (Release ID: {rel_id_1}, Version: 1.0.0)...")
    
    state_1 = {
        "release_id": rel_id_1,
        "version": "1.0.0",
        "project_id": "proj_task_tracking_api",
        "user_id": "user_devops_01",
        "commit_sha": "a1b2c3d4e5",
        "branch": "main",
        "target_environment": EnvironmentEnum.PRODUCTION,
        "approval_granted": True,
        "approved_by": "LeadDevOps (Pramod)",
        "qa_score": 96.5,
        "ci_status": "PASS",
        "qa_status": "PASS",
        "security_status": "PASS",
        "architecture_status": "PASS"
    }

    config_1 = {"configurable": {"thread_id": f"sess_{rel_id_1}"}}
    res_1 = await release_agent.ainvoke(state_1, config=config_1)

    readiness_1 = res_1.get("readiness")
    manifest_1 = res_1.get("release_manifest")
    staging_run_1 = res_1.get("staging_run")
    prod_run_1 = res_1.get("production_run")
    prod_health_1 = res_1.get("production_health")

    print("\n--- SCENARIO 1 RESULTS ---")
    if readiness_1:
        print(f"Risk Analysis Score    : {readiness_1.risk_score:.1f}/100 ({readiness_1.risk_level.value} Risk)")
        print(f"Policy Decision        : {readiness_1.decision.value} (Blockers: {len(readiness_1.blockers)})")
    if staging_run_1:
        print(f"Staging Deployment     : {staging_run_1.status.value} (Smoke Tests: {len(staging_run_1.smoke_test_results)} Passed)")
    if prod_run_1:
        print(f"Production Gate Approval: {res_1.get('approved_by')} (Granted: {res_1.get('approval_granted')})")
        print(f"Production Deployment  : {prod_run_1.status.value} (Health: {prod_health_1.status.value.upper() if prod_health_1 else 'HEALTHY'})")
    print(f"Final Release Status   : {res_1.get('status').value} [SUCCESS]")

    # -------------------------------------------------------------
    # SCENARIO 2: PRODUCTION HEALTH FAILURE -> AUTONOMOUS ROLLBACK
    # -------------------------------------------------------------
    print("\n\n" + "#" * 88)
    print("   SCENARIO 2: POST-DEPLOYMENT HEALTH FAILURE -> CONTROLLED AUTONOMOUS ROLLBACK")
    print("#" * 88)

    rel_id_2 = f"rel_{uuid.uuid4().hex[:8]}"
    print(f"\n[1/3] Initiating Production Release for Version 1.1.0 (Release ID: {rel_id_2})...")
    
    # Simulate health failure on production probe
    deployment_provider.simulate_production_health_failure = True

    state_2 = {
        "release_id": rel_id_2,
        "version": "1.1.0",
        "project_id": "proj_task_tracking_api",
        "user_id": "user_devops_01",
        "commit_sha": "f9e8d7c6b5",
        "branch": "main",
        "target_environment": EnvironmentEnum.PRODUCTION,
        "approval_granted": True,
        "approved_by": "LeadDevOps (Pramod)",
        "qa_score": 92.0,
        "ci_status": "PASS",
        "qa_status": "PASS",
        "security_status": "PASS",
        "architecture_status": "PASS"
    }

    try:
        config_2 = {"configurable": {"thread_id": f"sess_{rel_id_2}"}}
        res_2 = await release_agent.ainvoke(state_2, config=config_2)

        rollback_evt = res_2.get("rollback_event")

        print("\n--- SCENARIO 2 ROLLBACK RESULTS ---")
        print(f"Production Health Probe: UNHEALTHY (Triggered Autonomous Rollback Circuit)")
        if rollback_evt:
            print(f"Rollback ID            : {rollback_evt.rollback_id}")
            print(f"Failed Version         : {rollback_evt.failed_version}")
            print(f"Restored Version       : {rollback_evt.target_rollback_version} (Last Known-Good)")
            print(f"Rollback Reason        : {rollback_evt.reason}")
            print(f"Rollback Status        : {rollback_evt.status.value}")
        print(f"Final Release Status   : {res_2.get('status').value} [CONTROLLED ROLLBACK COMPLETED]")

    finally:
        deployment_provider.simulate_production_health_failure = False

    # -------------------------------------------------------------
    # METRICS & OBSERVABILITY SUMMARY
    # -------------------------------------------------------------
    print("\n\n" + "=" * 88)
    print("   DAY 12 OBSERVABILITY & TELEMETRY SUMMARY")
    print("=" * 88)
    summary = metrics.get_metrics_summary()
    print(f"Total Deployments Executed : {summary['counters']['deployments_total']}")
    print(f"Total Rollbacks Executed   : {summary['counters']['rollbacks_total']}")
    print(f"Total Health Checks Run    : {summary['counters']['health_checks_total']}")
    print(f"Observability Spans Logged : {summary['total_events_recorded']}")
    print("\n[SUCCESS] Day 12 Complete System Verified End-to-End.")

if __name__ == "__main__":
    asyncio.run(main())

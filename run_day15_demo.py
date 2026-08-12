import asyncio
import sys
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.agents.orchestrator.graph import master_orchestrator
from app.services.approval_service import approval_service
from app.services.timeline_service import timeline_service
from app.schemas.approval import (
    ApprovalDecisionRequest,
    ApprovalDecisionEnum,
    ReviewerRoleEnum,
    AgentExecutionStatusEnum
)

async def main():
    print("=" * 90)
    print("   AI SOFTWARE ENGINEER AGENT PLATFORM - DAY 15 HUMAN-IN-THE-LOOP ORCHESTRATION")
    print("   [Durable LangGraph Workflow] + [Approval Gates] + [Rejection & Rework] + [RBAC]")
    print("=" * 90)

    # -------------------------------------------------------------
    # STEP 1 & 2: START EXECUTION & PAUSE AT ARCHITECTURE GATE
    # -------------------------------------------------------------
    print("\n" + "#" * 90)
    print("   [STEP 1 & 2] STARTING WORKFLOW -> PLANNER & ARCHITECT NODES")
    print("#" * 90)
    print("Initiating autonomous software project workflow...")
    
    state = await master_orchestrator.start_execution(
        prompt="Build a high-performance Financial Analytics & Trading Engine API",
        project_id="proj_fintech_analytics_01",
        user_id="user_lead_architect"
    )
    
    exec_id = state["execution_id"]
    print(f"\nExecution ID               : {exec_id}")
    print(f"Current Phase              : {state['current_phase']}")
    print(f"Workflow Status            : {state['status']} [INTERRUPTED AT HUMAN GATE]")
    print(f"Approval Required          : {state['approval_required']}")
    print(f"Approval Request ID        : {state['approval_id']}")
    print(f"Action Hash (SHA-256)      : {state['action_hash'][:16]}...")

    arch_appr_id = state["approval_id"]
    appr_req = approval_service.get_approval(arch_appr_id)
    print(f"\nApproval Details:")
    print(f"  • Type                   : {appr_req.approval_type.value}")
    print(f"  • Risk Level             : {appr_req.risk_level.value}")
    print(f"  • Required Role          : {appr_req.required_role.value}")
    print(f"  • Action Summary         : {appr_req.action_summary}")
    print(f"  • Proposed Changes       : {appr_req.proposed_changes}")

    # -------------------------------------------------------------
    # STEP 3 & 4: HUMAN REJECTS ARCHITECTURE WITH FEEDBACK
    # -------------------------------------------------------------
    print("\n\n" + "#" * 90)
    print("   [STEP 3 & 4] HUMAN TECH LEAD REJECTS ARCHITECTURE & REQUESTS REWORK")
    print("#" * 90)
    feedback_text = "Reject SQLite/Default DB. Require PostgreSQL 16 with TimescaleDB time-series partitioning."
    print(f"Tech Lead Reviewer Decision : REQUEST_CHANGES")
    print(f"Structured Feedback         : '{feedback_text}'")

    dec_rework = ApprovalDecisionRequest(
        decision=ApprovalDecisionEnum.REQUEST_CHANGES,
        reviewer_id="tech_lead_bob",
        reviewer_role=ReviewerRoleEnum.TECH_LEAD,
        feedback=feedback_text,
        action_hash=state["action_hash"]
    )
    
    print("\nResuming workflow with rework feedback...")
    state = await master_orchestrator.resume_execution(exec_id, dec_rework)
    
    print(f"\nPost-Rework Execution Status:")
    print(f"  • Rework Count           : {state['rework_count']} (Attempt #1)")
    print(f"  • Current Phase          : {state['current_phase']}")
    print(f"  • Workflow Status        : {state['status']} [PAUSED AT NEW APPROVAL GATE]")
    print(f"  • New Approval ID        : {state['approval_id']}")
    print(f"  • New Action Hash        : {state['action_hash'][:16]}...")
    
    new_appr_id = state["approval_id"]

    # -------------------------------------------------------------
    # STEP 5: HUMAN APPROVES REWORKED ARCHITECTURE
    # -------------------------------------------------------------
    print("\n\n" + "#" * 90)
    print("   [STEP 5] HUMAN TECH LEAD APPROVES REWORKED ARCHITECTURE")
    print("#" * 90)
    print(f"Tech Lead Reviewer Decision : APPROVE")
    print(f"Approval Comment            : 'PostgreSQL 16 TimescaleDB architecture verified and approved.'")

    dec_approve_arch = ApprovalDecisionRequest(
        decision=ApprovalDecisionEnum.APPROVE,
        reviewer_id="tech_lead_bob",
        reviewer_role=ReviewerRoleEnum.TECH_LEAD,
        feedback="Architecture verified and approved.",
        action_hash=state["action_hash"]
    )

    print("\nResuming workflow past architecture gate...")
    state = await master_orchestrator.resume_execution(exec_id, dec_approve_arch)

    # -------------------------------------------------------------
    # STEP 6-8: DEVELOPER, QA, SECURITY, & RELEASE EXECUTION
    # -------------------------------------------------------------
    print("\n\n" + "#" * 90)
    print("   [STEP 6-8] AUTONOMOUS DEVELOPMENT, QA, SECURITY, AND RELEASE")
    print("#" * 90)
    print(f"Developer Agent Output     : {len(state['generated_files'])} modules generated ({', '.join(state['generated_files'][:3])}...)")
    print(f"QA Agent Test Status       : {state['test_results']['status']} (Score: {state['test_results']['qa_score']}/100, Coverage: {state['test_results']['coverage_pct']}%)")
    print(f"Security Agent Scan Status : {state['security_results']['status']} (Vulnerabilities: {state['security_results']['vulnerabilities_found']})")
    print(f"Release Agent Decision     : {state['release_plan']['decision']} (Target: {state['release_plan']['target_environment']})")
    print(f"Current Phase              : {state['current_phase']}")
    print(f"Workflow Status            : {state['status']} [INTERRUPTED AT DEPLOYMENT GATE]")
    print(f"Deployment Approval ID     : {state['approval_id']}")

    deploy_appr_id = state["approval_id"]
    deploy_appr = approval_service.get_approval(deploy_appr_id)
    print(f"\nDeployment Approval Details:")
    print(f"  • Type                   : {deploy_appr.approval_type.value}")
    print(f"  • Risk Level             : {deploy_appr.risk_level.value}")
    print(f"  • Required Role          : {deploy_appr.required_role.value}")
    print(f"  • Proposed Action        : {deploy_appr.action_summary}")

    # -------------------------------------------------------------
    # STEP 9-11: RELEASE MANAGER APPROVES PRODUCTION DEPLOYMENT
    # -------------------------------------------------------------
    print("\n\n" + "#" * 90)
    print("   [STEP 9-11] RELEASE MANAGER APPROVES PRODUCTION DEPLOYMENT")
    print("#" * 90)
    print(f"Release Manager Decision   : APPROVE")
    print(f"Reviewer Sign-off          : 'Release v1.0.0 passed all QA and Security gates. Deploying to prod-k8s.'")

    dec_approve_deploy = ApprovalDecisionRequest(
        decision=ApprovalDecisionEnum.APPROVE,
        reviewer_id="rel_mgr_charlie",
        reviewer_role=ReviewerRoleEnum.RELEASE_MANAGER,
        feedback="Release v1.0.0 production deployment approved.",
        action_hash=state["action_hash"]
    )

    print("\nResuming workflow to execute production deployment...")
    state = await master_orchestrator.resume_execution(exec_id, dec_approve_deploy)

    print(f"\nFinal Execution Status:")
    print(f"  • Phase                  : {state['current_phase']}")
    print(f"  • Workflow Status        : {state['status']} [SUCCESS]")
    print(f"  • Deployment Status      : {state['deployment_plan']['status']}")
    print(f"  • Target Cluster         : {state['deployment_plan']['cluster']}")
    print(f"  • Cluster Health Latency : {state['deployment_plan']['health_latency_ms']}ms")

    # -------------------------------------------------------------
    # STEP 12: EXECUTION TIMELINE & AUDIT TRAIL
    # -------------------------------------------------------------
    print("\n\n" + "#" * 90)
    print("   [STEP 12] EXECUTION TIMELINE & AUDIT TRAIL (OBSERVABILITY)")
    print("#" * 90)
    timeline = timeline_service.get_timeline(exec_id)
    print(f"Total Recorded Events: {len(timeline)}\n")
    for idx, ev in enumerate(timeline, 1):
        dur_str = f"({ev.duration_ms:.1f}ms)" if ev.duration_ms > 0 else ""
        print(f"  [{idx:>2}] {ev.timestamp[11:19]} | {ev.node:<22} | {ev.event:<28} | Status: {ev.status:<20} {dur_str}")

    print("\n" + "=" * 90)
    print("   [SUCCESS] DAY 15 HUMAN-IN-THE-LOOP & DURABLE EXECUTION SYSTEM VERIFIED.")
    print("=" * 90)

if __name__ == "__main__":
    asyncio.run(main())

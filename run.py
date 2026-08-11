import asyncio
import json
import sys
import uuid
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.agents.planner.graph import planner_agent
from app.schemas.plan import StructuredSoftwareDevelopmentPlan

async def main():
    print("=" * 85)
    print("   AI SOFTWARE ENGINEER AGENT PLATFORM - DETERMINISTIC PLANNER RUNNER")
    # Accepts any arbitrary software engineering requirement from CLI or generic default
    default_req = (
        "Build a modern software engineering platform with user authentication, "
        "project workspace management, task tracking, file asset storage, "
        "team collaboration, and analytics reporting."
    )
    requirement = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else default_req
    
    print(f"\nTarget Requirement:\n\"{requirement}\"\n")
    print("Executing Planner Agent...")
    
    initial_state = {
        "user_id": "user_swe_dev_01",
        "project_id": "proj_swe_001",
        "task_id": f"cli_task_{uuid.uuid4().hex[:8]}",
        "session_id": f"cli_sess_{uuid.uuid4().hex[:8]}",
        "original_requirement": requirement,
        "target_tech_stack": {
            "backend": "FastAPI",
            "database": "PostgreSQL",
            "cache": "Redis"
        },
        "project_type": "greenfield",
        "max_tasks": 50,
        "retry_count": 0
    }
    
    config = {"configurable": {"thread_id": initial_state["session_id"]}}
    
    print("[*] Executing LangGraph Planner Agent Workflow...")
    final_state = await planner_agent.ainvoke(initial_state, config=config)
    
    plan: StructuredSoftwareDevelopmentPlan = final_state.get("final_plan")
    
    if plan:
        print("\n" + "=" * 85)
        print(f"   PLAN GENERATED: {plan.project_information.project_name} (v{plan.project_information.version})")
        print("=" * 85)
        print(f"Domain & Target Env  : {plan.project_information.domain} [{plan.project_information.target_environment}]")
        print(f"Architecture Pattern : {plan.architecture_recommendation.pattern}")
        print(f"Bounded Contexts     : {', '.join(plan.architecture_recommendation.bounded_contexts)}")
        print(f"API Protocol         : {plan.recommended_technology_stack.api_protocol} ({plan.recommended_technology_stack.backend_framework})")
        approval = final_state.get("human_approval")
        approval_str = f"{approval.status} (by: {approval.approved_by})" if approval else "PENDING"
        print(f"Human Approval State : {approval_str}")
        print(f"Execution Status     : {final_state.get('execution_status')} | Validation Errors: {len(final_state.get('errors', []))}")
        
        print("\n--- 1. RECOMMENDED TECHNOLOGY STACK ---")
        print(f"  - Language & Framework: {plan.recommended_technology_stack.core_language} | {plan.recommended_technology_stack.backend_framework}")
        print(f"  - Relational Database : {plan.recommended_technology_stack.database}")
        print(f"  - Cache & Sessions    : {plan.recommended_technology_stack.cache_layer}")
        print(f"  - Authentication      : {plan.recommended_technology_stack.auth_mechanism}")

        print("\n--- 2. FUNCTIONAL & NON-FUNCTIONAL REQUIREMENTS ---")
        for fr in plan.requirements.functional:
            print(f"  [{fr.id}] ({fr.module}) {fr.title}")
            print(f"        Story: {fr.user_story}")
        for nfr in plan.requirements.non_functional:
            print(f"  [{nfr.id}] [{nfr.category}] {nfr.constraint} (Metric: {nfr.target_metric})")

        print("\n--- 3. PHASES & EXECUTION MILESTONES ---")
        for phase in plan.execution_metadata.phases:
            print(f"  Phase {phase.phase_number}: {phase.phase_name}")
            print(f"    Description: {phase.description}")
            print(f"    Tasks      : {', '.join(phase.task_ids)}")

        print("\n--- 4. ATOMIC TASK DIRECTED ACYCLIC GRAPH (DAG) ---")
        for task in plan.tasks:
            deps = f" (Depends on: {', '.join(task.upstream_dependencies)})" if task.upstream_dependencies else " (Root Task)"
            print(f"  [{task.task_id}] [{task.priority}] {task.title}{deps} - {task.estimated_hours}h [{task.complexity}]")
            print(f"        Files to Create: {', '.join(task.target_files.create) if task.target_files.create else 'None'}")
            for ac in task.acceptance_criteria:
                print(f"        - AC: {ac}")

        print("\n--- 5. RISK MATRIX & MITIGATION STRATEGIES ---")
        for risk in plan.risks:
            print(f"  [{risk.risk_id}] [{risk.severity} Severity] {risk.description}")
            print(f"        Mitigation: {risk.mitigation_strategy}")

        print(f"\n[SUCCESS] Plan generated strictly for '{plan.project_information.project_name}'.")
    else:
        print(f"\n[!] Planning finished with status: {final_state.get('execution_status')}")
        print(f"Errors: {final_state.get('errors')}")

if __name__ == "__main__":
    asyncio.run(main())

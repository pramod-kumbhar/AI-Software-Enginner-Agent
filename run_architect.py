import asyncio
import sys
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.agents.planner.graph import planner_agent
from app.agents.architect.graph import architect_agent
from app.schemas.architecture import StructuredSoftwareArchitecture

async def main():
    print("=" * 85)
    print("   AI SOFTWARE ENGINEER AGENT PLATFORM - ARCHITECT RUNNER")
    print("=" * 85)
    
    default_req = (
        "Build a modern software engineering platform with user authentication, "
        "project workspace management, task tracking, file asset storage, "
        "team collaboration, and analytics reporting."
    )
    requirement = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else default_req
        
    print(f"\n[1/2] Executing Planner Agent for: \"{requirement}\"...")
    plan_state = await planner_agent.ainvoke({
        "user_id": "user_cli",
        "project_id": "proj_cli",
        "task_id": "plan_cli_01",
        "session_id": "sess_plan_cli",
        "original_requirement": requirement
    }, config={"configurable": {"thread_id": "sess_plan_cli"}})
    
    plan = plan_state.get("final_plan")
    print(f"[*] Plan Generated: {plan.project_information.project_name} ({len(plan.tasks)} tasks)")
    
    print("\n[2/2] Executing Architect Agent...")
    arch_state = await architect_agent.ainvoke({
        "user_id": "user_cli",
        "project_id": "proj_cli",
        "planner_task_id": "plan_cli_01",
        "architect_task_id": "arch_cli_01",
        "session_id": "sess_arch_cli",
        "planner_output": plan
    }, config={"configurable": {"thread_id": "sess_arch_cli"}})
    
    arch: StructuredSoftwareArchitecture = arch_state.get("final_architecture")
    if arch:
        print("\n" + "=" * 85)
        print(f"   ARCHITECTURE GENERATED: {arch.project_information.project_name}")
        print("=" * 85)
        print(f"Pattern         : {arch.architecture_pattern}")
        print(f"Components ({len(arch.components)}) : {', '.join(c.name for c in arch.components)}")
        print(f"Entities ({len(arch.database_design.entities)})   : {', '.join(e.table_name for e in arch.database_design.entities)}")
        print(f"Endpoints ({len(arch.api_design.endpoints)})  : {len(arch.api_design.endpoints)} REST routes")
        print(f"Security        : {arch.security_design.authentication.mechanism}")
        print(f"Traceability    : {arch.validation_results.requirement_coverage_pct}% coverage ({len(arch.validation_results.traceability_matrix)} items mapped)")
        print(f"Approval Status : {arch.human_approval.status}")
        print("\n[SUCCESS] Software Architecture validated and ready for Developer Agent.")

if __name__ == "__main__":
    asyncio.run(main())

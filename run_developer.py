import asyncio
import sys
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.agents.planner.graph import planner_agent
from app.agents.architect.graph import architect_agent
from app.agents.developer.graph import developer_agent
from app.schemas.developer import ImplementationReport

async def main():
    print("=" * 85)
    print("   AI SOFTWARE ENGINEER AGENT PLATFORM - DEVELOPER RUNNER")
    print("=" * 85)
    
    default_req = (
        "Build a software engineering microservice with user authentication, "
        "document storage, full-text search, role-based access control, and analytics."
    )
    requirement = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else default_req
    
    print(f"\nTarget Requirement:\n\"{requirement}\"\n")
    
    # 1. Planner
    print("[1/3] Generating Software Development Plan...")
    plan_state = await planner_agent.ainvoke({
        "user_id": "user_swe_cli",
        "project_id": "proj_swe_cli",
        "task_id": "plan_task_swe_cli",
        "session_id": "sess_plan_swe_cli",
        "original_requirement": requirement
    }, config={"configurable": {"thread_id": "sess_plan_swe_cli"}})
    plan = plan_state.get("final_plan")
    
    # 2. Architect
    print("\n[2/3] Synthesizing Software Architecture...")
    arch_state = await architect_agent.ainvoke({
        "user_id": "user_swe_cli",
        "project_id": "proj_swe_cli",
        "planner_task_id": "plan_task_swe_cli",
        "architect_task_id": "arch_task_swe_cli",
        "session_id": "sess_arch_swe_cli",
        "planner_output": plan
    }, config={"configurable": {"thread_id": "sess_arch_swe_cli"}})
    arch = arch_state.get("final_architecture")
    
    # 3. Developer
    workspace_dir = "generated_projects/swe_service_cli"
    print(f"\n[3/3] Generating Source Code & Running Tests in Sandbox: {workspace_dir}...")
    dev_state = await developer_agent.ainvoke({
        "user_id": "user_swe_cli",
        "project_id": "proj_swe_cli",
        "architect_task_id": "arch_task_swe_cli",
        "developer_task_id": "dev_task_swe_cli",
        "session_id": "sess_dev_swe_cli",
        "approved_architecture": arch,
        "workspace_directory": workspace_dir
    }, config={"configurable": {"thread_id": "sess_dev_swe_cli"}})
    
    report: ImplementationReport = dev_state.get("implementation_report")
    print("\n" + "=" * 85)
    print(f"   CODE GENERATION COMPLETE: {report.project_name}")
    print("=" * 85)
    print(f"Status               : {report.implementation_status}")
    print(f"Files Created ({len(report.files_created)}) :")
    for f in report.files_created:
        print(f"  + {f}")
    print(f"Automated Tests Run  : {report.tests_executed} tests ({report.tests_passed} passed, {report.tests_failed} failed)")
    print(f"Human Approval State : {report.human_approval.status}")
    print("\n[SUCCESS] Developer Agent generated modular code and verified tests.")

if __name__ == "__main__":
    asyncio.run(main())

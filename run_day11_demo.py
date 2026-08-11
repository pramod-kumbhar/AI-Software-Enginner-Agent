import asyncio
import json
import sys
import uuid
import tempfile
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.agents.planner.graph import planner_agent
from app.agents.architect.graph import architect_agent
from app.agents.developer.graph import developer_agent
from app.agents.ci.graph import ci_repair_agent
from app.schemas.ci import CIRunStatusEnum
from app.services.filesystem import FilesystemService
from app.services.storage import storage_service
from app.mcp.client import MCPClient

async def main():
    print("=" * 85)
    print("   AI SOFTWARE ENGINEER AGENT PLATFORM - DAY 11 CI/CD & AUTONOMOUS REPAIR DEMO")
    print("   [CI Monitor Agent] + [Failure Analysis Agent] + [Bounded Autonomous Repair]")
    print("=" * 85)

    default_req = "Build a task management service with user registration, task creation, status updates, and priority tagging."
    requirement = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else default_req

    print(f"\nTarget Requirement:\n\"{requirement}\"\n")

    # 1. PLANNER
    print("[1/5] Executing Planner Agent...")
    plan_state = await planner_agent.ainvoke({
        "user_id": "user_devops_01",
        "project_id": "proj_task_mgr_day11",
        "task_id": "plan_task_day11",
        "session_id": "sess_plan_day11",
        "original_requirement": requirement
    }, config={"configurable": {"thread_id": "sess_plan_day11"}})
    plan = plan_state.get("final_plan")
    print(f"  -> Plan Created: {plan.project_information.project_name} ({len(plan.tasks)} atomic tasks)")

    # 2. ARCHITECT
    print("\n[2/5] Executing Architect Agent...")
    arch_state = await architect_agent.ainvoke({
        "user_id": "user_devops_01",
        "project_id": "proj_task_mgr_day11",
        "planner_task_id": "plan_task_day11",
        "architect_task_id": "arch_task_day11",
        "session_id": "sess_arch_day11",
        "planner_output": plan
    }, config={"configurable": {"thread_id": "sess_arch_day11"}})
    arch = arch_state.get("final_architecture")
    print(f"  -> Architecture Created: {len(arch.components)} components | Score: {arch.validation_results.validation_score}/100")

    # 3. DEVELOPER GENERATION
    workspace = "generated_projects/task_mgr_day11_demo"
    print(f"\n[3/5] Executing Developer Agent (Sandbox: {workspace})...")
    dev_state = await developer_agent.ainvoke({
        "developer_task_id": "dev_task_day11",
        "approved_architecture": arch,
        "workspace_directory": workspace,
        "session_id": "sess_dev_day11"
    }, config={"configurable": {"thread_id": "sess_dev_day11"}})
    print(f"  -> Generated {len(dev_state.get('generated_files', []))} files via MCP Tool Layer.")

    # 4. INTRODUCE INTENTIONAL FAILURE (Simulate CI Breakage)
    print("\n[4/5] Introducing Intentional Failure in Workspace (Broken Import in test)...")
    fs = FilesystemService(workspace_root=workspace)
    ok, test_content = fs.read_file("tests/modules/test_coremanagement.py")
    if ok:
        broken_content = "from app.modules.coremanagement.schemas import NonExistentBrokenSchema\n" + test_content
        fs.write_file("tests/modules/test_coremanagement.py", broken_content, overwrite=True)
        print("  -> Injected 'ImportError: cannot import name NonExistentBrokenSchema' into tests.")

    # 5. AUTONOMOUS CI/CD MONITORING & REPAIR WORKFLOW
    print("\n[5/5] Triggering CI/CD Monitoring & Autonomous Repair Workflow...")
    ci_state = await ci_repair_agent.ainvoke({
        "run_id": "ci_run_day11_demo",
        "project_id": "task_mgr_day11_demo",
        "user_id": "user_devops_01",
        "repository": "pramod-kumbhar/ai-software-engineer-agent",
        "branch": "ai-agent/task-mgr-day11-demo",
        "workflow_run_id": 100201,
        "workspace_directory": workspace,
        "attempt_count": 1,
        "max_attempts": 3
    }, config={"configurable": {"thread_id": "sess_ci_demo_day11"}})

    failure = ci_state.get("failure")
    repair_plan = ci_state.get("repair_plan")
    repair_res = ci_state.get("repair_result")
    qa_rep = ci_state.get("qa_report")

    print("\n" + "=" * 85)
    print("   DAY 11 AUTONOMOUS REPAIR WORKFLOW RESULTS")
    print("=" * 85)
    if failure:
        print(f"Detected CI Failure : {failure.failure_type.value} (Severity: {failure.severity.value})")
        print(f"Root Cause Analysis : {failure.root_cause}")
        print(f"Repairability Check : {failure.repairability.value}")
    if repair_plan:
        print(f"Repair Plan ID      : {repair_plan.repair_id} (Risk: {repair_plan.risk_level})")
        print(f"Target Changes      : {', '.join(repair_plan.required_changes)}")
    if qa_rep:
        print(f"QA Evaluation Score : {qa_rep.get('overall_score')}/100 (Passed: {qa_rep.get('passed')})")
    if repair_res:
        print(f"Final CI Status     : {repair_res.status.value}")
        print(f"Total Tests Run     : {repair_res.tests_passed}/{repair_res.tests_run} Passed")
        print(f"Repair Loop Attempts: {repair_res.attempt_number}/{repair_res.max_attempts} (Is Blocked: {repair_res.is_blocked})")

    print("\n[SUCCESS] Day 11 Autonomous CI/CD Monitoring & Repair Completed Successfully.")
    print("Note: Automatic merge is strictly BLOCKED. Changes are staged and ready for Human Code Review.")

if __name__ == "__main__":
    asyncio.run(main())

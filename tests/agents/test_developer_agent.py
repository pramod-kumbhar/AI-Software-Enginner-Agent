import asyncio
import tempfile
from app.agents.planner.graph import create_planner_graph
from app.agents.architect.graph import create_architect_graph
from app.agents.developer.graph import create_developer_graph
from app.schemas.developer import ImplementationReport

def test_developer_agent_code_generation_and_testing():
    async def _run():
        with tempfile.TemporaryDirectory() as tmpdir:
            planner = create_planner_graph()
            architect = create_architect_graph()
            developer = create_developer_graph()
            
            # 1. Planner
            plan_state = await planner.ainvoke({
                "user_id": "user_dev_01",
                "project_id": "proj_task_mgr",
                "task_id": "plan_task_mgr",
                "session_id": "sess_task_mgr",
                "original_requirement": "Build a task management system with user registration, task creation, status updates, and priority tagging."
            }, config={"configurable": {"thread_id": "sess_task_mgr"}})
            plan = plan_state.get("final_plan")
            assert plan is not None
            
            # 2. Architect
            arch_state = await architect.ainvoke({
                "user_id": "user_dev_01",
                "project_id": "proj_task_mgr",
                "planner_task_id": "plan_task_mgr",
                "architect_task_id": "arch_task_mgr",
                "session_id": "arch_sess_task_mgr",
                "planner_output": plan
            }, config={"configurable": {"thread_id": "arch_sess_task_mgr"}})
            arch = arch_state.get("final_architecture")
            assert arch is not None
            
            # 3. Developer
            dev_state = await developer.ainvoke({
                "user_id": "user_dev_01",
                "project_id": "proj_task_mgr",
                "architect_task_id": "arch_task_mgr",
                "developer_task_id": "dev_task_mgr",
                "session_id": "dev_sess_task_mgr",
                "approved_architecture": arch,
                "workspace_directory": tmpdir
            }, config={"configurable": {"thread_id": "dev_sess_task_mgr"}})
            
            report: ImplementationReport = dev_state.get("implementation_report")
            assert report is not None
            assert len(report.files_created) >= 5
            assert report.tests_executed > 0
            assert report.tests_passed == report.tests_executed
            assert report.implementation_status == "COMPLETED"
            assert report.human_approval.status == "PENDING"

    asyncio.run(_run())

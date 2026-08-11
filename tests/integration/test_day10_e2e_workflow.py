import asyncio
import tempfile
from app.agents.planner.graph import create_planner_graph
from app.agents.architect.graph import create_architect_graph
from app.agents.developer.graph import create_developer_graph
from app.mcp.client import MCPClient
from app.mcp.schemas import ToolExecutionStatusEnum

def test_day10_full_e2e_tool_and_github_pipeline():
    async def _run():
        with tempfile.TemporaryDirectory() as tmpdir:
            planner = create_planner_graph()
            architect = create_architect_graph()
            developer = create_developer_graph()
            
            # 1. Planner
            plan_state = await planner.ainvoke({
                "user_id": "user_e2e_day10",
                "project_id": "proj_task_mgr_day10",
                "task_id": "plan_task_day10",
                "session_id": "sess_plan_day10",
                "original_requirement": "Build a simple task management API with user, task creation, status updates, and task listing."
            }, config={"configurable": {"thread_id": "sess_plan_day10"}})
            plan = plan_state.get("final_plan")
            assert plan is not None
            
            # 2. Architect
            arch_state = await architect.ainvoke({
                "user_id": "user_e2e_day10",
                "project_id": "proj_task_mgr_day10",
                "planner_task_id": "plan_task_day10",
                "architect_task_id": "arch_task_day10",
                "session_id": "sess_arch_day10",
                "planner_output": plan
            }, config={"configurable": {"thread_id": "sess_arch_day10"}})
            arch = arch_state.get("final_architecture")
            assert arch is not None
            
            # 3. Developer (Routes through MCP Tool Layer)
            dev_state = await developer.ainvoke({
                "user_id": "user_e2e_day10",
                "project_id": "proj_task_mgr_day10",
                "architect_task_id": "arch_task_day10",
                "developer_task_id": "dev_task_day10",
                "session_id": "sess_dev_day10",
                "approved_architecture": arch,
                "workspace_directory": tmpdir
            }, config={"configurable": {"thread_id": "sess_dev_day10"}})
            report = dev_state.get("implementation_report")
            assert report is not None
            assert len(report.files_created) >= 5
            
            # 4. MCP Git Tools Workflow
            mcp_client = MCPClient(
                agent_name="DeveloperAgent",
                role="DEVELOPER",
                project_id="proj_task_mgr_day10",
                user_id="user_e2e_day10",
                workspace_root=tmpdir
            )
            
            # Git branch
            branch_res = await mcp_client.call_tool("git.create_branch", {"branch_name": "ai-agent/task-mgr-01"})
            assert branch_res.status == ToolExecutionStatusEnum.SUCCESS
            
            # Git status
            status_res = await mcp_client.call_tool("git.status", {})
            assert status_res.status == ToolExecutionStatusEnum.SUCCESS
            
            # Git commit with explicit approval token
            commit_res = await mcp_client.call_tool(
                "git.commit",
                {"message": "Implement Task Management API via MCP Layer"},
                approval_token="approved_human_01"
            )
            assert commit_res.status == ToolExecutionStatusEnum.SUCCESS
            
            # 5. MCP GitHub Tool PR creation with explicit approval token
            pr_res = await mcp_client.call_tool(
                "github.create_pull_request",
                {
                    "title": "AI Agent: Task Management API Implementation",
                    "body": "Automated PR with passing Pytest suites and AST verification.",
                    "head_branch": "ai-agent/task-mgr-01",
                    "base_branch": "main"
                },
                approval_token="approved_human_01"
            )
            assert pr_res.status == ToolExecutionStatusEnum.SUCCESS
            assert pr_res.result["pr_number"] > 0

    asyncio.run(_run())

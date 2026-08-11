import asyncio
from app.agents.planner.graph import create_planner_graph
from app.schemas.plan import StructuredSoftwareDevelopmentPlan

def test_planner_agent_generic_swe_platform():
    async def _run():
        agent = create_planner_graph()
        
        initial_state = {
            "user_id": "swe_dev_01",
            "project_id": "swe_proj_01",
            "task_id": "swe-task-001",
            "session_id": "swe-session-001",
            "original_requirement": "Build a cloud software engineering platform with code repository sync, pull request code review, automated testing runner, and deployment webhooks.",
            "target_tech_stack": {
                "backend": "FastAPI",
                "database": "PostgreSQL",
                "cache": "Redis"
            },
            "project_type": "greenfield",
            "max_tasks": 30,
            "retry_count": 0
        }
        
        config = {"configurable": {"thread_id": "swe-session-001"}}
        final_state = await agent.ainvoke(initial_state, config=config)
        
        assert final_state is not None
        assert final_state.get("is_dag_acyclic") is True
        assert final_state.get("execution_status") == "COMPLETED"
        assert len(final_state.get("errors", [])) == 0
        
        plan: StructuredSoftwareDevelopmentPlan = final_state.get("final_plan")
        assert plan is not None
        assert "Cloud Software Engineering" in plan.project_information.project_name
        
        fr_modules = [fr.module.lower() for fr in plan.requirements.functional]
        assert any("repository" in m or "code" in m for m in fr_modules)
        assert any("review" in m or "pull" in m for m in fr_modules)
        assert any("testing" in m or "runner" in m for m in fr_modules)
        assert any("webhook" in m or "deployment" in m for m in fr_modules)
        
        assert final_state.get("human_approval").status == "PENDING"

    asyncio.run(_run())

def test_planner_agent_healthcare_system():
    async def _run():
        agent = create_planner_graph()
        
        initial_state = {
            "user_id": "health_dev_01",
            "project_id": "health_proj_01",
            "task_id": "health-task-001",
            "session_id": "health-session-001",
            "original_requirement": "Build a hospital patient portal with appointment booking, doctor consultation, prescription history, and lab results.",
            "target_tech_stack": {
                "backend": "FastAPI",
                "database": "PostgreSQL",
                "cache": "Redis"
            },
            "project_type": "greenfield",
            "max_tasks": 30,
            "retry_count": 0
        }
        
        config = {"configurable": {"thread_id": "health-session-001"}}
        final_state = await agent.ainvoke(initial_state, config=config)
        
        plan: StructuredSoftwareDevelopmentPlan = final_state.get("final_plan")
        assert plan is not None
        assert "Hospital" in plan.project_information.project_name
        
        fr_modules = [fr.module.lower() for fr in plan.requirements.functional]
        assert any("appointment" in m or "booking" in m for m in fr_modules)
        assert any("prescription" in m or "consultation" in m for m in fr_modules)

    asyncio.run(_run())

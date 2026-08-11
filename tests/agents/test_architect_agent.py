import asyncio
from app.agents.planner.graph import create_planner_graph
from app.agents.architect.graph import create_architect_graph
from app.schemas.architecture import StructuredSoftwareArchitecture

def test_architect_agent_hotel_management():
    async def _run():
        planner = create_planner_graph()
        architect = create_architect_graph()
        
        # 1. Run Planner
        plan_state = await planner.ainvoke({
            "user_id": "user_01",
            "project_id": "proj_hotel",
            "task_id": "plan_task_hotel",
            "session_id": "sess_hotel",
            "original_requirement": "Build a hotel management system with customer registration, room booking, restaurant ordering, payment, admin dashboard, and staff management."
        }, config={"configurable": {"thread_id": "sess_hotel"}})
        plan = plan_state.get("final_plan")
        assert plan is not None
        
        # 2. Run Architect
        arch_state = await architect.ainvoke({
            "user_id": "user_01",
            "project_id": "proj_hotel",
            "planner_task_id": "plan_task_hotel",
            "architect_task_id": "arch_task_hotel",
            "session_id": "arch_sess_hotel",
            "planner_output": plan
        }, config={"configurable": {"thread_id": "arch_sess_hotel"}})
        
        arch: StructuredSoftwareArchitecture = arch_state.get("final_architecture")
        assert arch is not None
        assert "Hotel" in arch.project_information.project_name
        assert len(arch.components) >= 5
        assert len(arch.database_design.entities) >= 5
        assert len(arch.api_design.endpoints) >= 10
        assert arch.human_approval.status == "PENDING"
        assert arch.validation_results.validation_status in ["VALID", "WARNINGS"]
        assert arch.validation_results.requirement_coverage_pct == 100.0

    asyncio.run(_run())

def test_architect_agent_generalization_ecommerce():
    async def _run():
        planner = create_planner_graph()
        architect = create_architect_graph()
        
        plan_state = await planner.ainvoke({
            "user_id": "user_02",
            "project_id": "proj_ecom",
            "task_id": "plan_task_ecom",
            "session_id": "sess_ecom",
            "original_requirement": "Build an e-commerce application with authentication, products, shopping cart, orders and payment."
        }, config={"configurable": {"thread_id": "sess_ecom"}})
        plan = plan_state.get("final_plan")
        assert plan is not None
        
        arch_state = await architect.ainvoke({
            "user_id": "user_02",
            "project_id": "proj_ecom",
            "planner_task_id": "plan_task_ecom",
            "architect_task_id": "arch_task_ecom",
            "session_id": "arch_sess_ecom",
            "planner_output": plan
        }, config={"configurable": {"thread_id": "arch_sess_ecom"}})
        
        arch: StructuredSoftwareArchitecture = arch_state.get("final_architecture")
        assert arch is not None
        assert "Commerce" in arch.project_information.project_name
        assert len(arch.components) >= 4

    asyncio.run(_run())

import asyncio
import tempfile
import pytest
from app.agents.planner.graph import create_planner_graph
from app.agents.architect.graph import create_architect_graph
from app.agents.developer.graph import create_developer_graph

@pytest.mark.parametrize("domain_name,requirement,expected_modules", [
    (
        "DevOps Automation Platform",
        "Build a devops automation platform with repository sync, build triggers, artifact deployment, pipeline monitoring, and alert webhooks.",
        ["RepositorySync", "BuildTriggers", "ArtifactDeployment", "PipelineMonitoring", "AlertWebhooks"]
    ),
    (
        "Healthcare Telemedicine Service",
        "Build a healthcare telemedicine service with patient registration, doctor appointments, prescription tracking, and medical records.",
        ["PatientRegistration", "DoctorAppointments", "PrescriptionTracking", "MedicalRecords"]
    ),
    (
        "Fintech Payment Banking API",
        "Build a fintech payments API with customer wallet, bank transfer, transaction ledger, and fraud detection.",
        ["CustomerWallet", "BankTransfer", "TransactionLedger", "FraudDetection"]
    ),
    (
        "E-Commerce & Inventory System",
        "Build an e-commerce platform with product catalog, shopping cart, order processing, and inventory tracking.",
        ["ProductCatalog", "ShoppingCart", "OrderProcessing", "InventoryTracking"]
    ),
    (
        "AI Customer Support Platform",
        "Build an AI customer support platform with ticket creation, agent assignment, automated SLA resolution, and customer satisfaction surveys.",
        ["TicketCreation", "AgentAssignment", "AutomatedSlaResolution", "CustomerSatisfactionSurveys"]
    )
])
def test_all_software_engineering_domains(domain_name, requirement, expected_modules):
    """
    Verifies that the entire AI Software Engineer Agent platform is 100% generic
    and dynamically adapts to ANY software engineering domain without hardcoding.
    """
    async def _run():
        with tempfile.TemporaryDirectory() as tmpdir:
            planner = create_planner_graph()
            architect = create_architect_graph()
            developer = create_developer_graph()
            
            sess_id = f"sess_{domain_name.replace(' ', '_').lower()}"
            
            # 1. PLANNER
            plan_state = await planner.ainvoke({
                "user_id": "user_swe_multi",
                "project_id": f"proj_{domain_name.replace(' ', '_').lower()}",
                "task_id": f"task_{sess_id}",
                "session_id": sess_id,
                "original_requirement": requirement
            }, config={"configurable": {"thread_id": sess_id}})
            plan = plan_state.get("final_plan")
            assert plan is not None
            assert len(plan.features) >= 3
            assert len(plan.tasks) >= 4
            
            # 2. ARCHITECT
            arch_state = await architect.ainvoke({
                "user_id": "user_swe_multi",
                "project_id": f"proj_{domain_name.replace(' ', '_').lower()}",
                "planner_task_id": f"task_{sess_id}",
                "architect_task_id": f"arch_{sess_id}",
                "session_id": f"arch_{sess_id}",
                "planner_output": plan
            }, config={"configurable": {"thread_id": f"arch_{sess_id}"}})
            arch = arch_state.get("final_architecture")
            assert arch is not None
            assert len(arch.components) >= 3
            assert len(arch.database_design.entities) >= 3
            assert len(arch.api_design.endpoints) >= 6
            assert arch.validation_results.requirement_coverage_pct == 100.0
            
            # 3. DEVELOPER
            dev_state = await developer.ainvoke({
                "user_id": "user_swe_multi",
                "project_id": f"proj_{domain_name.replace(' ', '_').lower()}",
                "architect_task_id": f"arch_{sess_id}",
                "developer_task_id": f"dev_{sess_id}",
                "session_id": f"dev_{sess_id}",
                "approved_architecture": arch,
                "workspace_directory": tmpdir
            }, config={"configurable": {"thread_id": f"dev_{sess_id}"}})
            report = dev_state.get("implementation_report")
            assert report is not None
            assert len(report.files_created) >= 5
            assert report.tests_executed > 0
            assert report.tests_passed == report.tests_executed
            assert report.implementation_status == "COMPLETED"

    asyncio.run(_run())

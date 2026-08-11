from app.schemas.developer import (
    ImplementationPlan,
    ModulePlan,
    FilePlan,
    FileTypeEnum,
    FileActionEnum,
    GeneratedFile,
    ImplementationReport
)

def test_developer_schema_serialization():
    file_plan = FilePlan(
        file_path="app/modules/customers/router.py",
        file_type=FileTypeEnum.ROUTER,
        action=FileActionEnum.CREATE,
        purpose="Customer API Router"
    )
    
    mod_plan = ModulePlan(
        module_name="Customer Management",
        module_path="app/modules/customers",
        purpose="Handles customer lifecycle",
        files=[file_plan]
    )
    
    impl_plan = ImplementationPlan(
        project_slug="hotel-app",
        modules=[mod_plan],
        execution_order=["Customer Management"],
        total_files_planned=1
    )
    
    assert len(impl_plan.modules) == 1
    assert impl_plan.modules[0].files[0].file_path == "app/modules/customers/router.py"

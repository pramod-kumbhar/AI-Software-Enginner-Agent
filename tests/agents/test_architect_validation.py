from app.schemas.plan import FunctionalReq, NonFunctionalReq
from app.schemas.architecture import (
    ArchitectureComponent,
    DatabaseDesign,
    DatabaseEntity,
    APIDesign,
    APIEndpoint,
    SecurityDesign,
    TestStrategy,
    DeploymentStrategy
)
from app.agents.architect.validator import architecture_validator

def test_architecture_validation_100pct_coverage():
    frs = [
        FunctionalReq(id="FR-01", module="Customer", title="Customer Registration", user_story="", business_rules=[]),
        FunctionalReq(id="FR-02", module="Booking", title="Room Booking", user_story="", business_rules=[])
    ]
    nfrs = [
        NonFunctionalReq(id="NFR-01", category="SECURITY", constraint="TLS 1.3", target_metric="A+")
    ]
    components = [
        ArchitectureComponent(component_id="COMP-01", name="Customer Module", responsibility="Customer management", module_path="app/modules/customer/"),
        ArchitectureComponent(component_id="COMP-02", name="Booking Module", responsibility="Room bookings", module_path="app/modules/booking/")
    ]
    db_design = DatabaseDesign(entities=[
        DatabaseEntity(entity_id="ENT-01", table_name="customers", description=""),
        DatabaseEntity(entity_id="ENT-02", table_name="bookings", description="")
    ])
    api_design = APIDesign(endpoints=[
        APIEndpoint(endpoint_id="API-01", path="/api/v1/customers", summary="", module="Customer"),
        APIEndpoint(endpoint_id="API-02", path="/api/v1/bookings", summary="", module="Booking")
    ])
    sec_design = SecurityDesign()
    test_design = TestStrategy()
    deploy_design = DeploymentStrategy()
    
    val_res = architecture_validator.audit_architecture(
        functional_reqs=frs,
        non_functional_reqs=nfrs,
        components=components,
        db_design=db_design,
        api_design=api_design,
        security_design=sec_design,
        test_strategy=test_design,
        deployment_strategy=deploy_design
    )
    
    assert val_res.validation_status in ["VALID", "WARNINGS"]
    assert val_res.requirement_coverage_pct == 100.0
    assert len(val_res.traceability_matrix) == 2

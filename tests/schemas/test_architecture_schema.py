from app.schemas.architecture import (
    StructuredSoftwareArchitecture,
    ProjectInformation,
    ArchitecturePatternEnum,
    HighLevelDesign,
    LowLevelDesign,
    FolderStructureBlueprint
)

def test_architecture_schema_serialization():
    proj_info = ProjectInformation(
        project_name="Test Hotel System",
        project_slug="test-hotel-system",
        summary="Test summary",
        domain="Hospitality"
    )
    
    arch = StructuredSoftwareArchitecture(
        project_information=proj_info,
        architecture_pattern=ArchitecturePatternEnum.MODULAR_MONOLITH,
        architecture_overview="Test overview",
        high_level_design=HighLevelDesign(
            system_overview="HLD overview",
            c4_context_diagram_description="C4 description",
            data_flow_overview="Data flow"
        ),
        low_level_design=LowLevelDesign(
            package_structure="Package structure"
        ),
        folder_structure=FolderStructureBlueprint()
    )
    
    dumped = arch.model_dump()
    assert dumped["project_information"]["project_name"] == "Test Hotel System"
    assert dumped["architecture_pattern"] == ArchitecturePatternEnum.MODULAR_MONOLITH.value
    assert dumped["human_approval"]["status"] == "PENDING"

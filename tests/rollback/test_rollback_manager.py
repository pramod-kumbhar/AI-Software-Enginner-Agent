from app.schemas.release import (
    ReleaseStatusEnum,
    EnvironmentEnum,
    ReleaseReadiness
)
from app.services.rollback_manager import rollback_manager
from app.services.storage import storage_service

def test_rollback_to_previous_known_good_version():
    # Setup previous known-good release in storage
    storage_service.save_release("rel_v1_good", {
        "release_id": "rel_v1_good",
        "version": "1.0.0",
        "release_status": ReleaseStatusEnum.RELEASED.value
    })

    # Execute rollback from failed version 1.1.0
    success, event, msg = rollback_manager.execute_rollback(
        release_id="rel_v2_failed",
        failed_version="1.1.0",
        environment=EnvironmentEnum.PRODUCTION,
        target_version="1.0.0",
        reason="Health check degradation"
    )

    assert success is True
    assert event is not None
    assert event.target_rollback_version == "1.0.0"
    assert event.status == ReleaseStatusEnum.ROLLED_BACK

def test_rollback_same_version_blocked():
    success, event, msg = rollback_manager.execute_rollback(
        release_id="rel_invalid",
        failed_version="1.0.0",
        target_version="1.0.0"
    )
    assert success is False
    assert event is None
    assert "blocked" in msg.lower()

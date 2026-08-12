import threading
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.schemas.approval import ApprovalRequest
from app.core.logger import get_logger

logger = get_logger("notification_service")

class NotificationService:
    """
    Local & Extensible Human Notification Engine.
    Emits alerts when human approval is required, approved, rejected, or expired.
    Works offline with zero paid API dependencies.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(NotificationService, cls).__new__(cls)
                cls._instance._notifications: List[Dict[str, Any]] = []
            return cls._instance

    def notify_approval_required(self, approval_req: ApprovalRequest) -> None:
        with self._lock:
            notification = {
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "type": "APPROVAL_REQUIRED",
                "approval_id": approval_req.approval_id,
                "execution_id": approval_req.execution_id,
                "approval_type": approval_req.approval_type.value,
                "risk_level": approval_req.risk_level.value,
                "required_role": approval_req.required_role.value,
                "summary": approval_req.action_summary,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self._notifications.append(notification)
            logger.info(
                f"[NOTIFICATION] Human Approval Required! ID={approval_req.approval_id} "
                f"Type={approval_req.approval_type.value} Role={approval_req.required_role.value} "
                f"Summary='{approval_req.action_summary}'"
            )

    def notify_approval_resolved(self, approval_req: ApprovalRequest) -> None:
        with self._lock:
            notification = {
                "notification_id": f"notif_{uuid.uuid4().hex[:12]}",
                "type": "APPROVAL_RESOLVED",
                "approval_id": approval_req.approval_id,
                "execution_id": approval_req.execution_id,
                "status": approval_req.status.value,
                "reviewed_by": approval_req.reviewed_by,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            self._notifications.append(notification)
            logger.info(
                f"[NOTIFICATION] Approval Resolved! ID={approval_req.approval_id} "
                f"Status={approval_req.status.value} By={approval_req.reviewed_by}"
            )

    def get_notifications(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._notifications)

notification_service = NotificationService()

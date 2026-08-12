import threading
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.schemas.approval import TimelineEvent
from app.core.logger import get_logger

logger = get_logger("timeline_service")

class TimelineService:
    """
    Thread-safe Execution Timeline and Observability Event Engine.
    Tracks every node transition, approval lifecycle step, agent rework, and tool execution.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TimelineService, cls).__new__(cls)
                cls._instance._events: Dict[str, List[TimelineEvent]] = {}
            return cls._instance

    def record_event(
        self,
        execution_id: str,
        thread_id: str,
        node: str,
        event: str,
        status: str,
        actor: str = "System",
        duration_ms: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TimelineEvent:
        with self._lock:
            event_id = f"evt_{uuid.uuid4().hex[:12]}"
            ev = TimelineEvent(
                event_id=event_id,
                execution_id=execution_id,
                thread_id=thread_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                node=node,
                event=event,
                status=status,
                actor=actor,
                duration_ms=duration_ms,
                metadata=metadata or {}
            )
            if execution_id not in self._events:
                self._events[execution_id] = []
            self._events[execution_id].append(ev)
            logger.info(f"TIMELINE EVENT: [{execution_id}] Node={node} Event={event} Status={status} ({duration_ms:.1f}ms)")
            return ev

    def get_timeline(self, execution_id: str) -> List[TimelineEvent]:
        with self._lock:
            events = self._events.get(execution_id, [])
            return sorted(events, key=lambda x: x.timestamp)

    def get_all_events_count(self) -> int:
        with self._lock:
            return sum(len(v) for v in self._events.values())

timeline_service = TimelineService()

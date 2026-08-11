import time
import uuid
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from app.core.security import SecretMasker
from app.core.logging import logger

class MetricsRegistry:
    """
    Thread-safe in-memory metrics registry capturing latency, counts, errors,
    deployments, rollbacks, and health states.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricsRegistry, cls).__new__(cls)
                cls._instance._counters: Dict[str, int] = {
                    "http_requests_total": 0,
                    "http_errors_total": 0,
                    "deployments_total": 0,
                    "deployments_failed_total": 0,
                    "rollbacks_total": 0,
                    "health_checks_total": 0,
                    "health_checks_failed_total": 0,
                    "agent_executions_total": 0,
                    "tool_calls_total": 0,
                    "tool_failures_total": 0,
                    "ci_failures_total": 0,
                    "repair_attempts_total": 0
                }
                cls._instance._gauges: Dict[str, float] = {
                    "last_deployment_duration_seconds": 0.0,
                    "last_qa_score": 100.0,
                    "last_release_risk_score": 0.0,
                    "system_health_status": 1.0 # 1.0 = healthy, 0.5 = degraded, 0.0 = unhealthy
                }
                cls._instance._events: List[Dict[str, Any]] = []
            return cls._instance

    def increment(self, metric_name: str, value: int = 1) -> None:
        with self._lock:
            if metric_name in self._counters:
                self._counters[metric_name] += value
            else:
                self._counters[metric_name] = value

    def set_gauge(self, metric_name: str, value: float) -> None:
        with self._lock:
            self._gauges[metric_name] = value

    def record_event(self, event_type: str, metadata: Dict[str, Any]) -> None:
        with self._lock:
            sanitized = SecretMasker.sanitize_dict(metadata)
            sanitized["event_type"] = event_type
            sanitized["timestamp"] = datetime.now(timezone.utc).isoformat()
            self._events.append(sanitized)

    def get_metrics_summary(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "total_events_recorded": len(self._events),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

metrics = MetricsRegistry()

class TraceContext:
    """
    Context manager propagating distributed trace headers and recording span execution metrics.
    """
    def __init__(
        self,
        operation_name: str,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        release_id: Optional[str] = None,
        agent_name: Optional[str] = None
    ):
        self.operation_name = operation_name
        self.trace_id = f"trace_{uuid.uuid4().hex[:12]}"
        self.span_id = f"span_{uuid.uuid4().hex[:8]}"
        self.project_id = project_id or "default_project"
        self.task_id = task_id or "default_task"
        self.release_id = release_id
        self.agent_name = agent_name or "System"
        self.start_time: float = 0.0
        self.duration_ms: float = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        logger.info(
            f"SPAN_START: [{self.operation_name}] trace_id={self.trace_id} "
            f"agent={self.agent_name} project={self.project_id} task={self.task_id}"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration_ms = round((time.perf_counter() - self.start_time) * 1000.0, 2)
        status = "ERROR" if exc_type else "SUCCESS"
        
        metrics.increment("http_requests_total" if "http" in self.operation_name.lower() else "agent_executions_total")
        if exc_type:
            metrics.increment("http_errors_total")
            
        metrics.record_event(
            event_type="SPAN_COMPLETED",
            metadata={
                "operation": self.operation_name,
                "trace_id": self.trace_id,
                "span_id": self.span_id,
                "project_id": self.project_id,
                "task_id": self.task_id,
                "release_id": self.release_id,
                "agent_name": self.agent_name,
                "duration_ms": self.duration_ms,
                "status": status,
                "error": str(exc_val) if exc_val else None
            }
        )
        logger.info(
            f"SPAN_END: [{self.operation_name}] status={status} duration={self.duration_ms}ms trace_id={self.trace_id}"
        )

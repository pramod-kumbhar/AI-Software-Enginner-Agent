import time
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from app.schemas.configuration import TokenUsageRecord, CostRecord, UsageSummary
from app.services.cost_calculator import cost_calculator
from app.services.storage import storage_service
from app.core.logging import logger

class UsageTracker:
    """
    Central Token Usage & Execution Telemetry Tracker.
    Records fine-grained metrics per request, agent, provider, project, and user.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._usage_records: List[TokenUsageRecord] = []
        self._cost_records: List[CostRecord] = []
        self._tool_calls: List[Dict[str, Any]] = []

    def record_llm_usage(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        latency_ms: float,
        agent: str = "DeveloperAgent",
        project_id: str = "default_project",
        user_id: str = "default_user",
        task_id: str = "default_task",
        status: str = "SUCCESS",
        trace_id: Optional[str] = None
    ) -> TokenUsageRecord:
        """Records an LLM invocation and computes its associated FinOps cost."""
        usage_id = f"usg_{int(datetime.now(timezone.utc).timestamp()*1000)}_{len(self._usage_records)}"
        total_tokens = input_tokens + output_tokens

        record = TokenUsageRecord(
            usage_id=usage_id,
            user_id=user_id,
            project_id=project_id,
            task_id=task_id,
            agent=agent,
            provider=provider,
            model=model,
            trace_id=trace_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=round(latency_ms, 2),
            status=status
        )

        cost_rec = cost_calculator.calculate_cost(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            usage_id=usage_id
        )

        with self._lock:
            self._usage_records.append(record)
            self._cost_records.append(cost_rec)

        # Persist into storage service
        storage_service.save_metadata(f"usage_{usage_id}", record.model_dump())
        storage_service.save_metadata(f"cost_{cost_rec.cost_id}", cost_rec.model_dump())

        logger.info(
            f"USAGE RECORDED: [{agent}] via {provider}/{model} -> {total_tokens} tokens ({input_tokens} in / {output_tokens} out), "
            f"Est. Cost: ${cost_rec.estimated_cost:.6f} USD (Latency: {latency_ms:.1f}ms)"
        )
        return record

    def record_tool_call(
        self,
        tool_name: str,
        agent: str,
        duration_ms: float,
        status: str,
        project_id: str = "default_project",
        task_id: str = "default_task",
        risk_level: str = "READ_ONLY",
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Records tool execution duration and status without storing sensitive arguments."""
        tool_rec = {
            "tool_call_id": f"tc_{int(datetime.now(timezone.utc).timestamp()*1000)}",
            "tool": tool_name,
            "agent": agent,
            "project_id": project_id,
            "task_id": task_id,
            "risk_level": risk_level,
            "duration_ms": round(duration_ms, 2),
            "status": status,
            "error": error,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        with self._lock:
            self._tool_calls.append(tool_rec)
        return tool_rec

    def get_project_usage(self, project_id: str) -> List[TokenUsageRecord]:
        with self._lock:
            return [r for r in self._usage_records if r.project_id == project_id]

    def get_user_usage(self, user_id: str) -> List[TokenUsageRecord]:
        with self._lock:
            return [r for r in self._usage_records if r.user_id == user_id]

    def get_task_usage(self, task_id: str) -> List[TokenUsageRecord]:
        with self._lock:
            return [r for r in self._usage_records if r.task_id == task_id]

    def get_project_cost(self, project_id: str) -> float:
        with self._lock:
            project_usages = {r.usage_id for r in self._usage_records if r.project_id == project_id}
            return sum(c.estimated_cost for c in self._cost_records if c.usage_id in project_usages)

    def get_user_cost(self, user_id: str) -> float:
        with self._lock:
            user_usages = {r.usage_id for r in self._usage_records if r.user_id == user_id}
            return sum(c.estimated_cost for c in self._cost_records if c.usage_id in user_usages)

    def get_project_daily_tokens(self, project_id: str) -> int:
        """Returns total tokens consumed by a project in the current UTC day."""
        today_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._lock:
            return sum(
                r.total_tokens for r in self._usage_records 
                if r.project_id == project_id and r.created_at.startswith(today_prefix)
            )

    def get_project_daily_cost(self, project_id: str) -> float:
        today_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._lock:
            project_usages = {
                r.usage_id for r in self._usage_records 
                if r.project_id == project_id and r.created_at.startswith(today_prefix)
            }
            return sum(c.estimated_cost for c in self._cost_records if c.usage_id in project_usages)

    def get_summary(self) -> UsageSummary:
        with self._lock:
            total_reqs = len(self._usage_records)
            if total_reqs == 0:
                return UsageSummary()

            total_in = sum(r.input_tokens for r in self._usage_records)
            total_out = sum(r.output_tokens for r in self._usage_records)
            total_toks = sum(r.total_tokens for r in self._usage_records)
            total_cost = sum(c.estimated_cost for c in self._cost_records)
            avg_lat = sum(r.latency_ms for r in self._usage_records) / total_reqs
            failed = sum(1 for r in self._usage_records if r.status != "SUCCESS")

            prov_breakdown: Dict[str, int] = {}
            for r in self._usage_records:
                prov_breakdown[r.provider] = prov_breakdown.get(r.provider, 0) + r.total_tokens

            model_breakdown: Dict[str, int] = {}
            for r in self._usage_records:
                model_breakdown[r.model] = model_breakdown.get(r.model, 0) + r.total_tokens

            agent_breakdown: Dict[str, int] = {}
            for r in self._usage_records:
                agent_breakdown[r.agent] = agent_breakdown.get(r.agent, 0) + r.total_tokens

            return UsageSummary(
                total_requests=total_reqs,
                total_input_tokens=total_in,
                total_output_tokens=total_out,
                total_tokens=total_toks,
                estimated_cost_usd=round(total_cost, 6),
                average_latency_ms=round(avg_lat, 2),
                failed_requests=failed,
                provider_breakdown=prov_breakdown,
                model_breakdown=model_breakdown,
                agent_breakdown=agent_breakdown
            )

usage_tracker = UsageTracker()

import threading
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from app.schemas.configuration import (
    QuotaStatusEnum,
    QuotaDecision,
    UsageAlert,
    AlertTypeEnum
)
from app.services.usage_tracker import usage_tracker
from app.core.config import settings
from app.core.logging import logger

class QuotaManager:
    """
    Central FinOps & Execution Guard Quota Manager.
    Enforces per-request, daily, and monthly token/dollar limits with deterministic BLOCK/WARNING decisions.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._alerts: List[UsageAlert] = []
        self._custom_limits: Dict[str, Dict[str, float]] = {}

    def set_project_limit(self, project_id: str, max_daily_tokens: Optional[int] = None, max_daily_cost: Optional[float] = None) -> None:
        with self._lock:
            if project_id not in self._custom_limits:
                self._custom_limits[project_id] = {}
            if max_daily_tokens is not None:
                self._custom_limits[project_id]["daily_tokens"] = float(max_daily_tokens)
            if max_daily_cost is not None:
                self._custom_limits[project_id]["daily_cost"] = max_daily_cost

    def check_request_quota(
        self,
        project_id: str,
        user_id: str,
        estimated_input_tokens: int = 100,
        estimated_cost_usd: float = 0.0
    ) -> QuotaDecision:
        """
        Pre-flight quota evaluation before executing an LLM inference call.
        Returns ALLOWED, WARNING, HIGH_USAGE, or BLOCKED.
        """
        # 1. Per-Request Token Limit Check
        max_per_req = float(settings.MAX_LLM_TOKENS_PER_REQUEST)
        if estimated_input_tokens > max_per_req:
            self._trigger_alert(user_id, project_id, AlertTypeEnum.TOKEN_THRESHOLD, max_per_req, estimated_input_tokens, "tokens", "HIGH")
            return QuotaDecision(
                decision=QuotaStatusEnum.BLOCKED,
                current_value=float(estimated_input_tokens),
                limit_value=max_per_req,
                unit="tokens",
                message=f"Request token estimate ({estimated_input_tokens}) exceeds maximum allowed per request ({int(max_per_req)})."
            )

        # 2. Project Daily Token Limit Check
        current_daily_tokens = float(usage_tracker.get_project_daily_tokens(project_id))
        max_daily_tokens = self._custom_limits.get(project_id, {}).get("daily_tokens", float(settings.MAX_PROJECT_TOKENS_PER_DAY))
        
        projected_tokens = current_daily_tokens + estimated_input_tokens
        if projected_tokens > max_daily_tokens:
            self._trigger_alert(user_id, project_id, AlertTypeEnum.DAILY_LIMIT, max_daily_tokens, projected_tokens, "tokens", "CRITICAL")
            return QuotaDecision(
                decision=QuotaStatusEnum.BLOCKED,
                current_value=projected_tokens,
                limit_value=max_daily_tokens,
                unit="tokens",
                message=f"Project daily token quota exceeded: {int(projected_tokens)} / {int(max_daily_tokens)} tokens used."
            )

        # 3. Project Daily Dollar Budget Check
        current_daily_cost = usage_tracker.get_project_daily_cost(project_id)
        max_daily_cost = self._custom_limits.get(project_id, {}).get("daily_cost", float(settings.DAILY_COST_LIMIT_USD))
        
        projected_cost = current_daily_cost + estimated_cost_usd
        if projected_cost > max_daily_cost:
            self._trigger_alert(user_id, project_id, AlertTypeEnum.COST_THRESHOLD, max_daily_cost, projected_cost, "USD", "CRITICAL")
            return QuotaDecision(
                decision=QuotaStatusEnum.BLOCKED,
                current_value=round(projected_cost, 4),
                limit_value=max_daily_cost,
                unit="USD",
                message=f"Project daily dollar budget exceeded: ${projected_cost:.2f} / ${max_daily_cost:.2f} USD."
            )

        # 4. Usage Threshold Evaluation (0-50% ALLOWED, 50-80% WARNING, 80-100% HIGH_USAGE)
        token_ratio = projected_tokens / max_daily_tokens if max_daily_tokens > 0 else 0.0
        cost_ratio = projected_cost / max_daily_cost if max_daily_cost > 0 else 0.0
        max_ratio = max(token_ratio, cost_ratio)

        if max_ratio >= 0.8:
            return QuotaDecision(
                decision=QuotaStatusEnum.HIGH_USAGE,
                current_value=projected_tokens,
                limit_value=max_daily_tokens,
                unit="tokens",
                message=f"High project quota utilization ({max_ratio*100:.1f}% consumed)."
            )
        elif max_ratio >= 0.5:
            return QuotaDecision(
                decision=QuotaStatusEnum.WARNING,
                current_value=projected_tokens,
                limit_value=max_daily_tokens,
                unit="tokens",
                message=f"Moderate project quota utilization ({max_ratio*100:.1f}% consumed)."
            )

        return QuotaDecision(
            decision=QuotaStatusEnum.ALLOWED,
            current_value=projected_tokens,
            limit_value=max_daily_tokens,
            unit="tokens",
            message="Quota check passed."
        )

    def check_agent_iteration_quota(self, agent_name: str, current_iteration: int) -> Tuple[bool, str]:
        """Prevents runaway infinite loops in LangGraph agent workflows."""
        max_iters = settings.MAX_AGENT_ITERATIONS
        if current_iteration > max_iters:
            logger.error(f"AGENT LOOP BLOCKED: Agent '{agent_name}' exceeded maximum allowed iterations ({max_iters}).")
            return False, f"Agent '{agent_name}' reached maximum iteration limit ({max_iters})."
        return True, "Iteration within limits."

    def check_repair_attempt_quota(self, finding_id: str, attempt_number: int) -> Tuple[bool, str]:
        """Enforces circuit breaker on automated repair attempts."""
        max_attempts = settings.MAX_REPAIR_ATTEMPTS
        if attempt_number > max_attempts:
            logger.error(f"REPAIR LOOP BLOCKED: Finding '{finding_id}' exceeded max repair attempts ({max_attempts}).")
            return False, f"Maximum repair attempts ({max_attempts}) reached for {finding_id}."
        return True, "Repair attempt permitted."

    def _trigger_alert(
        self,
        user_id: str,
        project_id: str,
        alert_type: AlertTypeEnum,
        threshold: float,
        current_val: float,
        unit: str,
        severity: str
    ) -> None:
        alert = UsageAlert(
            alert_id=f"alt_{int(datetime.now(timezone.utc).timestamp()*1000)}",
            user_id=user_id,
            project_id=project_id,
            alert_type=alert_type,
            threshold=threshold,
            current_value=round(current_val, 4),
            unit=unit,
            severity=severity,
            status="ACTIVE"
        )
        with self._lock:
            self._alerts.append(alert)
        logger.warning(f"QUOTA ALERT [{severity}]: {alert_type.value} triggered for project '{project_id}' ({current_val} >= {threshold} {unit})")

    def list_alerts(self, project_id: Optional[str] = None) -> List[UsageAlert]:
        with self._lock:
            if project_id:
                return [a for a in self._alerts if a.project_id == project_id]
            return list(self._alerts)

quota_manager = QuotaManager()

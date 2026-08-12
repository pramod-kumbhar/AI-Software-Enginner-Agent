from typing import List, Dict, Any
from fastapi import APIRouter, Body
from app.services.quota_manager import quota_manager
from app.services.usage_tracker import usage_tracker
from app.core.config import settings
from app.schemas.configuration import QuotaDecision, UsageAlert

router = APIRouter(prefix="/quotas", tags=["Quota & Budget Management"])

@router.get("/project/{project_id}", response_model=Dict[str, Any])
async def get_project_quota_status(project_id: str):
    """Returns current project token and dollar utilization against configured thresholds."""
    daily_tokens = usage_tracker.get_project_daily_tokens(project_id)
    daily_cost = usage_tracker.get_project_daily_cost(project_id)
    
    max_tokens = float(settings.MAX_PROJECT_TOKENS_PER_DAY)
    max_cost = float(settings.DAILY_COST_LIMIT_USD)

    token_pct = round((daily_tokens / max_tokens) * 100.0, 2) if max_tokens > 0 else 0.0
    cost_pct = round((daily_cost / max_cost) * 100.0, 2) if max_cost > 0 else 0.0

    return {
        "project_id": project_id,
        "daily_tokens_used": daily_tokens,
        "daily_tokens_limit": int(max_tokens),
        "tokens_utilization_pct": token_pct,
        "daily_cost_used_usd": round(daily_cost, 4),
        "daily_cost_limit_usd": max_cost,
        "cost_utilization_pct": cost_pct,
        "status": "HEALTHY" if max(token_pct, cost_pct) < 80.0 else "WARNING"
    }

@router.get("/alerts", response_model=List[UsageAlert])
async def list_quota_alerts(project_id: str = None):
    """Lists active quota and budget alerts."""
    return quota_manager.list_alerts(project_id=project_id)

@router.post("/check", response_model=QuotaDecision)
async def check_quota_preflight(
    project_id: str = Body(..., embed=True),
    user_id: str = Body(default="default_user", embed=True),
    estimated_tokens: int = Body(default=100, embed=True),
    estimated_cost_usd: float = Body(default=0.0, embed=True)
):
    """Pre-flight check to verify if a request is permitted within active quotas."""
    return quota_manager.check_request_quota(
        project_id=project_id,
        user_id=user_id,
        estimated_input_tokens=estimated_tokens,
        estimated_cost_usd=estimated_cost_usd
    )

from typing import Dict, Any
from fastapi import APIRouter
from app.services.usage_tracker import usage_tracker
from app.services.cost_calculator import cost_calculator

router = APIRouter(prefix="/cost", tags=["Cost & FinOps Tracking"])

@router.get("/summary", response_model=Dict[str, Any])
async def get_cost_summary():
    """Returns global estimated FinOps cost summary."""
    summary = usage_tracker.get_summary()
    return {
        "total_estimated_cost_usd": summary.estimated_cost_usd,
        "total_tokens": summary.total_tokens,
        "provider_breakdown": summary.provider_breakdown,
        "currency": "USD"
    }

@router.get("/project/{project_id}", response_model=Dict[str, Any])
async def get_project_cost(project_id: str):
    """Returns total estimated cost in USD for a project."""
    cost = usage_tracker.get_project_cost(project_id)
    tokens = usage_tracker.get_project_daily_tokens(project_id)
    return {
        "project_id": project_id,
        "estimated_cost_usd": round(cost, 6),
        "daily_tokens_consumed": tokens,
        "currency": "USD"
    }

@router.get("/user/{user_id}", response_model=Dict[str, Any])
async def get_user_cost(user_id: str):
    """Returns total estimated cost in USD for a user."""
    cost = usage_tracker.get_user_cost(user_id)
    return {
        "user_id": user_id,
        "estimated_cost_usd": round(cost, 6),
        "currency": "USD"
    }

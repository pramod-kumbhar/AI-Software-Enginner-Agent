from typing import List
from fastapi import APIRouter
from app.services.usage_tracker import usage_tracker
from app.schemas.configuration import TokenUsageRecord, UsageSummary

router = APIRouter(prefix="/usage", tags=["Token Usage Tracking"])

@router.get("/summary", response_model=UsageSummary)
async def get_global_usage_summary():
    """Returns aggregated token usage, latency, and agent breakdowns across all projects."""
    return usage_tracker.get_summary()

@router.get("/project/{project_id}", response_model=List[TokenUsageRecord])
async def get_project_usage(project_id: str):
    """Returns all token usage records for a specific project."""
    return usage_tracker.get_project_usage(project_id)

@router.get("/user/{user_id}", response_model=List[TokenUsageRecord])
async def get_user_usage(user_id: str):
    """Returns all token usage records for a specific user."""
    return usage_tracker.get_user_usage(user_id)

@router.get("/task/{task_id}", response_model=List[TokenUsageRecord])
async def get_task_usage(task_id: str):
    """Returns all token usage records for a specific task."""
    return usage_tracker.get_task_usage(task_id)

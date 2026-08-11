import uuid
from fastapi import APIRouter, HTTPException
from app.schemas.plan import PlannerInputRequest, PlannerResponse
from app.agents.planner.graph import planner_agent
from app.core.logging import logger

router = APIRouter(prefix="/plans", tags=["Planner Agent"])

# In-memory store for quick task lookups
TASK_STORE = {}

@router.post("/generate", response_model=PlannerResponse)
async def generate_plan(request: PlannerInputRequest):
    """
    Triggers the autonomous Planner Agent workflow to create a machine-deterministic development plan.
    """
    task_id = request.task_id or str(uuid.uuid4())
    session_id = f"session_{task_id}"
    
    logger.info(f"Received planning request for Task ID: {task_id}")
    
    initial_state = {
        "user_id": request.user_id or "user_default_01",
        "project_id": request.project_id or "proj_default_01",
        "task_id": task_id,
        "session_id": session_id,
        "original_requirement": request.raw_requirement,
        "target_tech_stack": request.target_tech_stack or {},
        "project_type": request.project_type or "greenfield",
        "max_tasks": request.max_tasks or 50,
        "retry_count": 0
    }
    
    config = {"configurable": {"thread_id": session_id}}
    
    try:
        final_state = await planner_agent.ainvoke(initial_state, config=config)
        
        response = PlannerResponse(
            task_id=task_id,
            session_id=session_id,
            current_agent=final_state.get("current_agent", "PLANNER_AGENT"),
            execution_status=final_state.get("execution_status", "UNKNOWN"),
            plan=final_state.get("final_plan"),
            clarifications=final_state.get("clarifications"),
            human_approval=final_state.get("human_approval"),
            errors=final_state.get("errors"),
            retry_count=final_state.get("retry_count", 0)
        )
        
        TASK_STORE[task_id] = response
        if response.plan:
            from app.services.storage import storage_service
            storage_service.save_plan(task_id, response.plan)
        return response
        
    except Exception as e:
        logger.error(f"Error during plan generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Planning execution failed: {str(e)}")

@router.get("/{task_id}", response_model=PlannerResponse)
async def get_plan(task_id: str):
    """Retrieves the generated plan for a given task ID."""
    if task_id not in TASK_STORE:
        raise HTTPException(status_code=404, detail="Task ID not found")
    return TASK_STORE[task_id]

from app.api.v1.planner import router as planner_router
from app.api.v1.architect import router as architect_router
from app.api.v1.developer import router as developer_router
from app.api.v1.tools import router as tools_router
from app.api.v1.github import router as github_router
from app.api.v1.ci import router as ci_router, repairs_router
from app.api.v1.releases import router as releases_router
from app.api.v1.security import router as security_router

__all__ = [
    "planner_router",
    "architect_router",
    "developer_router",
    "tools_router",
    "github_router",
    "ci_router",
    "repairs_router",
    "releases_router",
    "security_router"
]

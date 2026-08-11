import sys
from pathlib import Path

# Add project root directory to sys.path so 'app' is always resolvable
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.api.v1.planner import router as planner_router
from app.api.v1.architect import router as architect_router
from app.api.v1.developer import router as developer_router
from app.api.v1.tools import router as tools_router
from app.api.v1.github import router as github_router
from app.api.v1.ci import router as ci_router, repairs_router
from app.api.v1.releases import router as releases_router
from app.api.v1.security import router as security_router
from app.services.health_service import health_service
from app.core.observability import metrics

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Autonomous AI Software Engineer Platform with Release Governance, Observability, Deployment, and Rollback.",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers for All Multi-Agent & Tool Layers
app.include_router(planner_router, prefix=settings.API_V1_STR)
app.include_router(architect_router, prefix=settings.API_V1_STR)
app.include_router(developer_router, prefix=settings.API_V1_STR)
app.include_router(tools_router, prefix=settings.API_V1_STR)
app.include_router(github_router, prefix=settings.API_V1_STR)
app.include_router(ci_router, prefix=settings.API_V1_STR)
app.include_router(repairs_router, prefix=settings.API_V1_STR)
app.include_router(releases_router, prefix=settings.API_V1_STR)
app.include_router(security_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def health_check():
    return health_service.check_health().model_dump()

@app.get("/health/live", tags=["Health"])
async def liveness_probe():
    return {"status": "healthy", "alive": True, "service": settings.PROJECT_NAME}

@app.get("/health/ready", tags=["Health"])
async def readiness_probe():
    health = health_service.check_health()
    return {"status": health.status.value, "ready": health.readiness, "version": settings.VERSION}

@app.get("/health/dependencies", tags=["Health"])
async def dependencies_probe():
    health = health_service.check_health()
    return {"dependencies": health.dependencies, "latency_ms": health.latency_ms}

@app.get("/metrics", tags=["Observability"])
async def get_metrics():
    return metrics.get_metrics_summary()


if __name__ == "__main__":
    import uvicorn
    # Points app_dir to the Implementation root so 'app.main:app' resolves from any directory
    uvicorn.run("app.main:app", app_dir=str(ROOT_DIR), host="0.0.0.0", port=8000, reload=True)

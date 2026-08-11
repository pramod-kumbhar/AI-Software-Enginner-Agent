from fastapi import FastAPI
from app.core.config import settings
from app.modules.string.router import router as string_router

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# Register Domain Routers
app.include_router(string_router, prefix=settings.API_PREFIX)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
)

# Set up CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}

from app.api import projects, upload, super_resolution, assistant, validation, map

app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(upload.router, prefix="/api/v1/projects", tags=["upload"])
app.include_router(super_resolution.router, prefix="/api/v1/projects", tags=["super-resolution"])
app.include_router(assistant.router, prefix="/api/v1/assistant", tags=["assistant"])
app.include_router(validation.router, prefix="/api/v1/validation", tags=["validation"])
app.include_router(map.router, prefix="/api/v1/map", tags=["map"])

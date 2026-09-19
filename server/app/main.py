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

# ─── Existing routers ──────────────────────────────────────────────────────────
from app.api import projects, upload, super_resolution, assistant, validation, map, gee

app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(upload.router, prefix="/api/v1/projects", tags=["upload"])
app.include_router(super_resolution.router, prefix="/api/v1/projects", tags=["super-resolution"])
app.include_router(assistant.router, prefix="/api/v1/projects", tags=["assistant"])
app.include_router(validation.router, prefix="/api/v1/validation", tags=["validation"])
app.include_router(map.router, prefix="/api/v1/map", tags=["map"])
app.include_router(gee.router, prefix="/api/v1/projects", tags=["Google Earth Engine"])

# ─── New intelligence routers ──────────────────────────────────────────────────
from app.api import intelligence, change_detection, anomalies, risk, export

app.include_router(intelligence.router, prefix="/api/v1/intelligence", tags=["intelligence"])
app.include_router(change_detection.router, prefix="/api/v1/change-detection", tags=["change-detection"])
app.include_router(anomalies.router, prefix="/api/v1/anomalies", tags=["anomalies"])
app.include_router(risk.router, prefix="/api/v1/risk", tags=["risk"])
app.include_router(export.router, prefix="/api/v1/export", tags=["export"])

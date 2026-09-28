from contextlib import asynccontextmanager
import subprocess
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Running database migrations from FastAPI lifespan...", flush=True)
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from app.database import Base
        import app.models  # ensure models are loaded
        
        engine = create_async_engine(settings.DATABASE_URI)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("SQLAlchemy create_all complete.", flush=True)
        
        # Also run alembic to ensure the version table is up to date
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        print("Migrations complete.", flush=True)
    except Exception as e:
        print(f"Migrations failed: {e}", flush=True)
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
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

# ─── Real-time satellite data (CDSE + Open-Meteo) ──────────────────────────────
from app.api import realtime
app.include_router(realtime.router, prefix="/api/v1/realtime", tags=["realtime"])

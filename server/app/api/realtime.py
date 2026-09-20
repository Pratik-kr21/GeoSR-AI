"""
realtime.py
===========
FastAPI router for real-time Sentinel-2 satellite data acquisition.

Endpoints:
  POST /api/v1/realtime/fetch/{project_id}         — fetch & store scene
  GET  /api/v1/realtime/latest/{project_id}         — latest stored scene
  POST /api/v1/realtime/fetch-and-process/{project_id} — fetch + SR + Intel pipeline
"""

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.database import get_db
from app.models import Observation, AnalysisJob, Project
from app.services.storage_service import storage_service
from app.services.realtime_service import realtime_service
from app.services.raster_service import raster_service
from app.workers.tasks import run_super_resolution_pipeline
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

TEMP_DIR = "/tmp/geosrai_realtime"
os.makedirs(TEMP_DIR, exist_ok=True)


# ─── Request / Response schemas ────────────────────────────────────────────────

class RealtimeFetchRequest(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Centre latitude in decimal degrees.")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Centre longitude in decimal degrees.")
    buffer_km: Optional[float] = Field(5.0, ge=0.5, le=100, description="Search radius around centre in kilometres.")
    bbox: Optional[list[float]] = Field(None, description="Bounding box [minLon, minLat, maxLon, maxLat]. Overrides lat/lon/buffer.")
    days_back: int   = Field(30,  ge=1,   le=365,  description="How many days into the past to search.")
    max_cloud_cover: int = Field(20, ge=0, le=100,  description="Maximum acceptable cloud cover percentage.")


class RealtimeFetchResponse(BaseModel):
    observation_id: int
    object_name: str
    filename: str
    acquisition_date: Optional[str]
    cloud_cover: Optional[float]
    bounds: Optional[list]
    weather_summary: dict
    message: str


class FetchAndProcessResponse(BaseModel):
    observation_id: int
    object_name: str
    sr_job_id: str
    acquisition_date: Optional[str]
    cloud_cover: Optional[float]
    weather_summary: dict
    message: str


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _check_cdse_available():
    """Raise 503 if CDSE is not configured."""
    if not settings.CDSE_ENABLED:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "cdse_not_configured",
                "message": (
                    "Real-time Sentinel-2 fetching is not configured. "
                    "Add CDSE_CLIENT_ID and CDSE_CLIENT_SECRET to your .env file. "
                    "Register free at https://dataspace.copernicus.eu/ and create an "
                    "OAuth client at https://shapps.dataspace.copernicus.eu/dashboard/#/account/settings"
                ),
            }
        )


async def _fetch_upload_create_observation(
    project_id: int,
    req: RealtimeFetchRequest,
    db: AsyncSession,
) -> tuple:
    """
    Core logic shared by /fetch and /fetch-and-process:
    1. Download GeoTIFF from CDSE
    2. Upload to MinIO
    3. Fetch weather from Open-Meteo
    4. Create Observation record in PostgreSQL
    Returns (observation_db_object, object_name, acquisition_date, cloud_cover, weather, bounds)
    """
    # 1. Download GeoTIFF from CDSE (blocking I/O → runs in thread)
    import asyncio
    loop = asyncio.get_event_loop()
    try:
        local_path, acquisition_date, cloud_cover, bounds = await loop.run_in_executor(
            None,
            lambda: realtime_service.fetch_sentinel2_geotiff(
                lat=req.latitude,
                lon=req.longitude,
                buffer_km=req.buffer_km,
                bbox=req.bbox,
                days_back=req.days_back,
                max_cloud_cover=req.max_cloud_cover,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except RuntimeError as e:
        err_str = str(e)
        if "No Sentinel-2 scene" in err_str:
            raise HTTPException(status_code=404, detail={
                "error": "no_scene_found",
                "message": err_str,
            })
        elif "authentication failed" in err_str.lower() or "CDSE credentials" in err_str:
            raise HTTPException(status_code=401, detail={
                "error": "cdse_auth_failed",
                "message": err_str,
            })
        else:
            raise HTTPException(status_code=502, detail={
                "error": "cdse_download_failed",
                "message": err_str,
            })

    # 2. Upload to MinIO
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"realtime_{timestamp}.tif"
    object_name = f"projects/{project_id}/inputs/{filename}"

    try:
        storage_service.upload_file(local_path, object_name)
    except Exception as e:
        try:
            os.remove(local_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail={
            "error": "storage_failed",
            "message": f"GeoTIFF downloaded successfully but MinIO upload failed: {e}",
        })

    # Clean up the local temp file now that it's in MinIO
    try:
        os.remove(local_path)
    except Exception:
        pass

    # 3. Fetch weather (non-blocking, always succeeds)
    # If using bbox, use center for weather
    w_lat = req.latitude if req.latitude is not None else ((req.bbox[1] + req.bbox[3]) / 2 if req.bbox else 0)
    w_lon = req.longitude if req.longitude is not None else ((req.bbox[0] + req.bbox[2]) / 2 if req.bbox else 0)
    weather = await realtime_service.fetch_weather_data(w_lat, w_lon)

    # 4. Extract raster metadata for the Observation record
    # We need to read it from MinIO — download to a quick temp path
    temp_meta_path = os.path.join(TEMP_DIR, f"meta_{uuid.uuid4()}.tif")
    try:
        storage_service.download_file(object_name, temp_meta_path)
        raster_meta = raster_service.read_metadata(temp_meta_path)
    except Exception as e:
        logger.warning(f"Could not read raster metadata: {e}")
        raster_meta = {}
    finally:
        try:
            os.remove(temp_meta_path)
        except Exception:
            pass

    # 5. Create Observation in PostgreSQL
    obs = Observation(
        project_id=project_id,
        object_name=object_name,
        satellite="Sentinel-2 L2A (CDSE)",
        cloud_percentage=cloud_cover,
        observation_date=acquisition_date,
        bands_count=raster_meta.get("count"),
        band_descriptions=raster_meta.get("band_descriptions"),
        bbox=bounds,
        crs=raster_meta.get("crs"),
        width=raster_meta.get("width"),
        height=raster_meta.get("height"),
    )
    db.add(obs)
    await db.commit()
    await db.refresh(obs)

    return obs, object_name, acquisition_date, cloud_cover, weather, bounds


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/status")
async def realtime_status():
    """
    Check if real-time Sentinel-2 fetching is enabled.
    Returns capability flags so the frontend can show/hide the feature.
    """
    return {
        "cdse_enabled": settings.CDSE_ENABLED,
        "open_meteo_available": True,   # Always available, no credentials needed
        "message": (
            "Real-time Sentinel-2 fetching is available."
            if settings.CDSE_ENABLED
            else "CDSE credentials not configured. Weather-only mode is active."
        ),
    }


@router.post("/fetch/{project_id}", response_model=RealtimeFetchResponse)
async def fetch_realtime_imagery(
    project_id: int,
    req: RealtimeFetchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch the most recent clear-sky Sentinel-2 scene for the given location,
    upload it to MinIO, and create an Observation record.

    Returns the observation ID, MinIO object name, acquisition date, cloud cover,
    and a live weather summary from Open-Meteo.
    """
    _check_cdse_available()

    # Verify project exists
    proj_result = await db.execute(select(Project).filter(Project.id == project_id))
    if not proj_result.scalars().first():
        raise HTTPException(status_code=404, detail="Project not found.")

    obs, object_name, acquisition_date, cloud_cover, weather, bounds = \
        await _fetch_upload_create_observation(project_id, req, db)

    return RealtimeFetchResponse(
        observation_id=obs.id,
        object_name=object_name,
        filename=object_name.split("/")[-1],
        acquisition_date=acquisition_date.isoformat() if acquisition_date else None,
        cloud_cover=cloud_cover,
        bounds=bounds,
        weather_summary={
            "available": weather["available"],
            "current_precip_mm": weather.get("current_precip_mm"),
            "total_7d_rain_mm": weather.get("total_7d_rain_mm"),
            "daily_breakdown": weather.get("daily_breakdown", [])[:7],
        },
        message=(
            f"Sentinel-2 scene from {acquisition_date.strftime('%Y-%m-%d') if acquisition_date else 'unknown date'} "
            f"({cloud_cover:.1f}% cloud cover) successfully fetched and stored."
        ),
    )


@router.get("/latest/{project_id}")
async def get_latest_realtime_observation(
    project_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Return the most recently fetched real-time observation for a project.
    The observation is identified by object_name starting with 'projects/{id}/inputs/realtime_'.
    """
    result = await db.execute(
        select(Observation)
        .filter(
            Observation.project_id == project_id,
            Observation.object_name.like(f"projects/{project_id}/inputs/realtime_%"),
        )
        .order_by(desc(Observation.created_at))
        .limit(1)
    )
    obs = result.scalars().first()

    if not obs:
        raise HTTPException(
            status_code=404,
            detail="No real-time observation found for this project. Use POST /fetch first."
        )

    return {
        "observation_id": obs.id,
        "object_name": obs.object_name,
        "filename": obs.object_name.split("/")[-1],
        "satellite": obs.satellite,
        "acquisition_date": obs.observation_date.isoformat() if obs.observation_date else None,
        "cloud_cover": obs.cloud_percentage,
        "bounds": obs.bbox,
        "crs": obs.crs,
        "width": obs.width,
        "height": obs.height,
        "bands_count": obs.bands_count,
        "created_at": obs.created_at.isoformat() if obs.created_at else None,
    }


@router.post("/fetch-and-process/{project_id}", response_model=FetchAndProcessResponse)
async def fetch_and_process_realtime(
    project_id: int,
    req: RealtimeFetchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Full pipeline:
    1. Fetch latest Sentinel-2 scene from CDSE
    2. Upload to MinIO
    3. Create Observation in PostgreSQL
    4. Fetch live weather from Open-Meteo
    5. Queue Super-Resolution Celery job
    6. Return observation ID + SR job ID for frontend polling

    The intelligence analysis (spectral indices, anomalies, risk) should be
    triggered separately via POST /intelligence/{project_id}/analyze after
    the SR job completes.
    """
    _check_cdse_available()

    # Verify project exists
    proj_result = await db.execute(select(Project).filter(Project.id == project_id))
    if not proj_result.scalars().first():
        raise HTTPException(status_code=404, detail="Project not found.")

    obs, object_name, acquisition_date, cloud_cover, weather, bounds = \
        await _fetch_upload_create_observation(project_id, req, db)

    # Queue Super-Resolution job
    sr_job_id = str(uuid.uuid4())
    output_object_name = object_name.replace("/inputs/", "/outputs/sr_")

    sr_job = AnalysisJob(
        id=sr_job_id,
        project_id=project_id,
        status="pending",
        input_resolution=10.0,
        target_resolution=2.5,
    )
    db.add(sr_job)
    await db.commit()

    run_super_resolution_pipeline.delay(
        job_id=sr_job_id,
        project_id=project_id,
        input_path=object_name,
        output_path=output_object_name,
    )

    logger.info(f"SR job {sr_job_id} queued for realtime observation {obs.id}")

    return FetchAndProcessResponse(
        observation_id=obs.id,
        object_name=object_name,
        sr_job_id=sr_job_id,
        acquisition_date=acquisition_date.isoformat() if acquisition_date else None,
        cloud_cover=cloud_cover,
        weather_summary={
            "available": weather["available"],
            "current_precip_mm": weather.get("current_precip_mm"),
            "total_7d_rain_mm": weather.get("total_7d_rain_mm"),
        },
        message=(
            f"Scene from {acquisition_date.strftime('%Y-%m-%d') if acquisition_date else 'unknown'} "
            f"fetched. Super-resolution job queued. Poll job {sr_job_id} for status."
        ),
    )


@router.get("/check-availability")
async def check_scene_availability(
    latitude: float,
    longitude: float,
    days_back: int = 30,
    max_cloud_cover: int = 20,
    buffer_km: float = 5.0,
):
    """
    Non-destructive catalog check: find out if a scene exists without downloading it.
    Returns scene metadata and weather summary. Fast (< 3 seconds).
    """
    result = await realtime_service.get_latest_available_scene(
        lat=latitude,
        lon=longitude,
        buffer_km=buffer_km,
        days_back=days_back,
        max_cloud_cover=max_cloud_cover,
    )
    return result


class HistoricalAnalysisRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    buffer_km: float = Field(5.0, ge=0.5, le=100)
    years: list[int]
    season_start: str = "01-01"
    season_end: str = "12-31"
    max_cloud_cover: int = 40

@router.post("/fetch-sar/{project_id}")
async def fetch_sar(project_id: int, req: RealtimeFetchRequest, db: AsyncSession = Depends(get_db)):
    _check_cdse_available()
    proj_result = await db.execute(select(Project).filter(Project.id == project_id))
    if not proj_result.scalars().first():
        raise HTTPException(status_code=404, detail="Project not found.")
        
    from app.workers.tasks import fetch_sar_background
    job_id = str(uuid.uuid4())
    
    task = fetch_sar_background.delay(
        job_id=job_id, project_id=project_id, 
        latitude=req.latitude or ((req.bbox[1] + req.bbox[3])/2 if req.bbox else 0), 
        longitude=req.longitude or ((req.bbox[0] + req.bbox[2])/2 if req.bbox else 0), 
        buffer_km=req.buffer_km, days_back=req.days_back, bbox=req.bbox
    )
    return {"job_id": task.id, "message": "SAR fetching and analysis started in background."}

@router.post("/fetch-dem/{project_id}")
async def fetch_dem(project_id: int, req: RealtimeFetchRequest, db: AsyncSession = Depends(get_db)):
    _check_cdse_available()
    proj_result = await db.execute(select(Project).filter(Project.id == project_id))
    if not proj_result.scalars().first():
        raise HTTPException(status_code=404, detail="Project not found.")
        
    from app.workers.tasks import fetch_dem_background
    job_id = str(uuid.uuid4())
    
    task = fetch_dem_background.delay(
        job_id=job_id, project_id=project_id, 
        latitude=req.latitude or ((req.bbox[1] + req.bbox[3])/2 if req.bbox else 0), 
        longitude=req.longitude or ((req.bbox[0] + req.bbox[2])/2 if req.bbox else 0), 
        buffer_km=req.buffer_km, bbox=req.bbox
    )
    return {"job_id": task.id, "message": "DEM fetching and processing started in background."}

@router.post("/fetch-cloudfree/{project_id}")
async def fetch_cloudfree(project_id: int, req: RealtimeFetchRequest, db: AsyncSession = Depends(get_db)):
    proj_result = await db.execute(select(Project).filter(Project.id == project_id))
    if not proj_result.scalars().first():
        raise HTTPException(status_code=404, detail="Project not found.")
        
    from app.workers.tasks import fetch_gee_composite_background
    job_id = str(uuid.uuid4())
    
    task = fetch_gee_composite_background.delay(
        job_id=job_id, project_id=project_id, 
        latitude=req.latitude or ((req.bbox[1] + req.bbox[3])/2 if req.bbox else 0), 
        longitude=req.longitude or ((req.bbox[0] + req.bbox[2])/2 if req.bbox else 0), 
        buffer_km=req.buffer_km, days_back=req.days_back, max_cloud_cover=req.max_cloud_cover,
        bbox=req.bbox
    )
    return {"job_id": task.id, "message": "GEE Composite fetch started in background."}

@router.post("/historical-analysis/{project_id}")
async def historical_analysis(project_id: int, req: HistoricalAnalysisRequest, db: AsyncSession = Depends(get_db)):
    proj_result = await db.execute(select(Project).filter(Project.id == project_id))
    if not proj_result.scalars().first():
        raise HTTPException(status_code=404, detail="Project not found.")
        
    from app.workers.tasks import run_historical_analysis
    job_id = str(uuid.uuid4())
    task = run_historical_analysis.delay(
        job_id=job_id, project_id=project_id, lat=req.latitude, lon=req.longitude, buffer_km=req.buffer_km,
        years=req.years, season_start=req.season_start, season_end=req.season_end
    )
    return {"job_id": task.id, "message": "Historical analysis started in background."}


@router.get("/jobs/{job_id}")
async def get_realtime_job_status(job_id: str):
    from app.workers.celery_app import celery_app
    from celery.result import AsyncResult
    task = AsyncResult(job_id, app=celery_app)
    
    if task.state == 'PENDING':
        return {"status": "pending"}
    elif task.state == 'SUCCESS':
        return task.result
    elif task.state == 'FAILURE':
        return {"status": "failed", "error": str(task.info)}
    else:
        return {"status": task.state.lower()}

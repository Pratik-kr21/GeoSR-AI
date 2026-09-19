import time
import asyncio
from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.workers.celery_app import celery_app
from app.services.inference_service import inference_service
from app.models import AnalysisJob
from app.config import settings

async def update_job_status(job_id: str, status: str):
    engine = create_async_engine(settings.DATABASE_URI, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        await session.execute(
            update(AnalysisJob).where(AnalysisJob.id == job_id).values(status=status)
        )
        await session.commit()
    await engine.dispose()

@celery_app.task(name="app.workers.tasks.run_super_resolution_pipeline")
def run_super_resolution_pipeline(job_id: str, project_id: int, input_path: str, output_path: str):
    """
    Background task to run the super-resolution AI model.
    """
    try:
        # Mark as processing
        asyncio.run(update_job_status(job_id, "processing"))
        
        # 1. Run PyTorch Super-Resolution Inference
        inference_service.run_super_resolution(input_path, output_path)
        
        # Mark as completed
        asyncio.run(update_job_status(job_id, "completed"))
        
        return {
            "job_id": job_id,
            "project_id": project_id,
            "status": "completed",
            "result_path": output_path
        }
    except Exception as e:
        print(f"Error in anomaly detection pipeline: {e}")
        asyncio.run(update_job_status(job_id, "failed"))
        raise e

@celery_app.task(name="app.workers.tasks.fetch_gee_imagery")
def fetch_gee_imagery(project_id: int, bbox: list, max_cloud_cover: int = 20):
    """
    Background task to fetch live imagery from Google Earth Engine.
    """
    from app.services.gee_service import gee_service
    
    print(f"Starting GEE fetch for bbox: {bbox}")
    result = gee_service.fetch_live_imagery(project_id, bbox, max_cloud_cover)
    
    if "error" in result:
        print(f"GEE Fetch failed: {result['error']}")
        # In a real system, we'd update a job status here so the frontend knows it failed
        return result
        
    print(f"Successfully fetched GEE imagery: {result['object_name']}")
    
    # Automatically trigger Super Resolution pipeline on the new image!
    import uuid
    from datetime import datetime
    
    new_job_id = str(uuid.uuid4())
    
    # Fire off the super resolution task
    run_super_resolution_pipeline.delay(
        job_id=new_job_id,
        project_id=project_id,
        input_path=result['object_name'],
        output_path=result['object_name'].replace("inputs/", "outputs/").replace(".tif", "_sr.tif")
    )
    
    return result


@celery_app.task(name="app.workers.tasks.fetch_and_process_realtime")
def fetch_and_process_realtime(project_id: int, latitude: float, longitude: float,
                                buffer_km: float = 5.0, days_back: int = 30,
                                max_cloud_cover: int = 20):
    """
    End-to-end real-time pipeline as a single Celery background task:
      1. Authenticate with CDSE and download the latest Sentinel-2 scene
      2. Upload the GeoTIFF to MinIO
      3. Create an Observation record in PostgreSQL
      4. Fetch live precipitation from Open-Meteo
      5. Queue a Super-Resolution job
      6. Return combined status dict for the frontend to poll

    Use this from long-running background contexts. The HTTP endpoint
    /api/v1/realtime/fetch-and-process runs the same logic inline (async).
    """
    import uuid
    from datetime import datetime, timezone

    from app.services.realtime_service import realtime_service
    from app.services.storage_service import storage_service
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from app.models import Observation, AnalysisJob

    async def _run():
        # 1. Download from CDSE (blocking, run in current thread)
        try:
            local_path, acquisition_date, cloud_cover, bounds = \
                realtime_service.fetch_sentinel2_geotiff(
                    lat=latitude, lon=longitude,
                    buffer_km=buffer_km, days_back=days_back,
                    max_cloud_cover=max_cloud_cover,
                )
        except Exception as e:
            return {"status": "failed", "error": str(e), "stage": "cdse_download"}

        # 2. Upload to MinIO
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"realtime_{timestamp}.tif"
        object_name = f"projects/{project_id}/inputs/{filename}"
        try:
            storage_service.upload_file(local_path, object_name)
        except Exception as e:
            return {"status": "failed", "error": str(e), "stage": "minio_upload"}

        # 3. Fetch weather (non-blocking async)
        weather = await realtime_service.fetch_weather_data(latitude, longitude)

        # 4. Create Observation in DB
        engine = create_async_engine(settings.DATABASE_URI, echo=False)
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        obs_id = None
        async with async_session() as session:
            obs = Observation(
                project_id=project_id,
                object_name=object_name,
                satellite="Sentinel-2 L2A (CDSE)",
                cloud_percentage=cloud_cover,
                observation_date=acquisition_date,
                bbox=bounds,
            )
            session.add(obs)
            await session.commit()
            await session.refresh(obs)
            obs_id = obs.id

            # 5. Create SR job record
            sr_job_id = str(uuid.uuid4())
            sr_job = AnalysisJob(
                id=sr_job_id, project_id=project_id,
                status="pending", input_resolution=10.0, target_resolution=2.5,
            )
            session.add(sr_job)
            await session.commit()

        await engine.dispose()

        # 6. Queue SR pipeline
        output_path = object_name.replace("/inputs/", "/outputs/sr_")
        run_super_resolution_pipeline.delay(
            job_id=sr_job_id,
            project_id=project_id,
            input_path=object_name,
            output_path=output_path,
        )

        return {
            "status": "processing",
            "observation_id": obs_id,
            "object_name": object_name,
            "sr_job_id": sr_job_id,
            "acquisition_date": acquisition_date.isoformat() if acquisition_date else None,
            "cloud_cover": cloud_cover,
            "weather_available": weather.get("available", False),
            "total_7d_rain_mm": weather.get("total_7d_rain_mm"),
        }

    return asyncio.run(_run())

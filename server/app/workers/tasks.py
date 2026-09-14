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
        asyncio.run(update_job_status(job_id, "failed"))
        raise e

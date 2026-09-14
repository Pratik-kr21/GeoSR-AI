from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

from app.database import get_db
from app.models import AnalysisJob, Project
from app.workers.tasks import run_super_resolution_pipeline

router = APIRouter()

@router.post("/{project_id}/super-resolution")
async def start_super_resolution(project_id: int, object_name: str, db: AsyncSession = Depends(get_db)):
    # Check if project exists
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job_id = str(uuid.uuid4())
    
    # Create Analysis Job in DB
    new_job = AnalysisJob(
        id=job_id,
        project_id=project_id,
        status="pending",
        input_resolution=10.0,
        target_resolution=2.5
    )
    db.add(new_job)
    await db.commit()
    
    # Dispatch Celery Task
    input_object_name = object_name
    output_object_name = object_name.replace("/inputs/", "/outputs/sr_")
    
    run_super_resolution_pipeline.delay(
        job_id=job_id,
        project_id=project_id,
        input_path=input_object_name,
        output_path=output_object_name
    )
    
    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Super-resolution job has been added to the queue."
    }

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AnalysisJob).filter(AnalysisJob.id == job_id))
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {
        "job_id": job.id,
        "status": job.status,
        "input_resolution": job.input_resolution,
        "target_resolution": job.target_resolution
    }

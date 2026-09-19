from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List

from app.workers.tasks import fetch_gee_imagery

router = APIRouter()

class GEEFetchRequest(BaseModel):
    bbox: List[float] # [west, south, east, north]
    max_cloud_cover: int = 20

@router.post("/{project_id}/gee-fetch")
async def fetch_imagery_from_gee(project_id: int, request: GEEFetchRequest):
    if len(request.bbox) != 4:
        raise HTTPException(status_code=400, detail="Bounding box must contain exactly 4 coordinates [west, south, east, north]")
        
    # Dispatch the Celery task to fetch the image in the background
    fetch_gee_imagery.delay(
        project_id=project_id,
        bbox=request.bbox,
        max_cloud_cover=request.max_cloud_cover
    )
    
    return {
        "status": "processing",
        "message": "GEE Fetch triggered. Super Resolution will automatically start once downloaded."
    }

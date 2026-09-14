from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
import os

from app.services.storage_service import storage_service
from app.services.raster_service import raster_service

router = APIRouter()

@router.get("/{project_id}/outputs/{file_id}/bounds")
async def get_map_bounds(project_id: int, file_id: str):
    # Construct MinIO object name (e.g. from super_resolution)
    # The file_id here includes the "sr_" prefix or the original UUID
    object_name = f"projects/{project_id}/outputs/{file_id}"
    
    local_path = f"/tmp/bounds_{file_id}"
    try:
        storage_service.download_file(object_name, local_path)
        bounds_data = raster_service.get_reprojected_bounds(local_path)
        if "error" in bounds_data:
            raise HTTPException(status_code=400, detail=bounds_data["error"])
        return bounds_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)

@router.get("/{project_id}/outputs/{file_id}/thumbnail")
async def get_output_thumbnail(project_id: int, file_id: str):
    object_name = f"projects/{project_id}/outputs/{file_id}"
    local_path = f"/tmp/thumb_out_{file_id}"
    try:
        storage_service.download_file(object_name, local_path)
        jpeg_bytes = raster_service.generate_thumbnail(local_path, size=1024)
        return Response(content=jpeg_bytes, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)

@router.get("/{project_id}/inputs/{file_id}/thumbnail")
async def get_input_thumbnail(project_id: int, file_id: str):
    object_name = f"projects/{project_id}/inputs/{file_id}"
    local_path = f"/tmp/thumb_in_{file_id}"
    try:
        storage_service.download_file(object_name, local_path)
        jpeg_bytes = raster_service.generate_thumbnail(local_path, size=1024)
        return Response(content=jpeg_bytes, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)

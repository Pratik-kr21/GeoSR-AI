from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
import os
import uuid

from app.services.storage_service import storage_service
from app.services.raster_service import raster_service

router = APIRouter()

UPLOAD_DIR = "/tmp/geosrai_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/{project_id}/upload")
async def upload_image(project_id: int, file: UploadFile = File(...)):
    if not file.filename.endswith(('.tif', '.tiff')):
        raise HTTPException(status_code=400, detail="Only GeoTIFF files are supported")
    
    file_id = str(uuid.uuid4())
    temp_file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    # 1. Save to temporary file
    with open(temp_file_path, "wb") as buffer:
        buffer.write(await file.read())
        
    # 2. Extract metadata
    metadata = raster_service.read_metadata(temp_file_path)
    if "error" in metadata:
        os.remove(temp_file_path)
        raise HTTPException(status_code=400, detail=f"Invalid GeoTIFF: {metadata['error']}")
        
    # 3. Upload to MinIO
    object_name = f"projects/{project_id}/inputs/{file_id}_{file.filename}"
    try:
        storage_service.upload_file(temp_file_path, object_name)
    except Exception as e:
        os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Failed to upload to storage: {str(e)}")
        
    # 4. Cleanup
    os.remove(temp_file_path)
    
    # Calculate approx resolution if bounds are available (width/lon, height/lat) - simplified
    # In reality rasterio transform provides this
    return {
        "file_id": file_id,
        "filename": file.filename,
        "object_name": object_name,
        "dimensions": [metadata.get("width"), metadata.get("height")],
        "bands": metadata.get("count"),
        "crs": metadata.get("crs"),
        "bounds": metadata.get("bounds")
    }

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

@router.get("/{project_id}/inputs/{file_id}/bounds")
async def get_input_bounds(project_id: int, file_id: str):
    object_name = f"projects/{project_id}/inputs/{file_id}"
    local_path = f"/tmp/bounds_in_{file_id}"
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
        jpeg_bytes = raster_service.generate_thumbnail(local_path, size=None)
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
        jpeg_bytes = raster_service.generate_thumbnail(local_path, size=None)
        return Response(content=jpeg_bytes, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)

@router.get("/{project_id}/outputs/{file_id}/download")
async def get_output_download(project_id: int, file_id: str):
    """
    Returns a presigned URL to download the full enhanced GeoTIFF directly from MinIO.
    """
    object_name = f"projects/{project_id}/outputs/{file_id}"
    try:
        url = storage_service.get_presigned_url(object_name)
        return {"download_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Analytics Heatmap Endpoints ──────────────────────────────────────────────

@router.get("/{project_id}/ndvi-heatmap")
async def get_ndvi_heatmap(project_id: int, object_name: str):
    """
    Generate an NDVI heatmap PNG (RdYlGn colormap) from the input GeoTIFF.
    Returns PNG bytes for Leaflet ImageOverlay, plus bounds.
    """
    import numpy as np
    from app.services.spectral_service import spectral_service

    local_path = f"/tmp/heatmap_ndvi_{object_name.replace('/', '_')}"
    try:
        storage_service.download_file(object_name, local_path)
        bounds_data = raster_service.get_reprojected_bounds(local_path)
        si_data = spectral_service.compute_spectral_indices(object_name)

        ndvi_arr = si_data.get("ndvi_array")
        if ndvi_arr is None:
            raise HTTPException(
                status_code=422,
                detail=f"NDVI unavailable: {si_data.get('ndvi_available', 'unknown reason')}"
            )

        png_bytes = raster_service.generate_colormap_overlay(
            ndvi_arr, cmap_name="RdYlGn", vmin=-0.2, vmax=0.9
        )
        return Response(content=png_bytes, media_type="image/png", headers={
            "X-Bounds": str(bounds_data.get("bounds", [])),
            "X-NDVI-Mean": str(round(float(np.nanmean(ndvi_arr)), 4)),
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)


@router.get("/{project_id}/ndwi-heatmap")
async def get_ndwi_heatmap(project_id: int, object_name: str):
    """
    Generate an NDWI heatmap PNG (Blues_r colormap) from the input GeoTIFF.
    """
    import numpy as np
    from app.services.spectral_service import spectral_service

    local_path = f"/tmp/heatmap_ndwi_{object_name.replace('/', '_')}"
    try:
        storage_service.download_file(object_name, local_path)
        bounds_data = raster_service.get_reprojected_bounds(local_path)
        si_data = spectral_service.compute_spectral_indices(object_name)

        ndwi_arr = si_data.get("ndwi_array")
        if ndwi_arr is None:
            raise HTTPException(
                status_code=422,
                detail=f"NDWI unavailable: {si_data.get('ndwi_available', 'unknown reason')}"
            )

        png_bytes = raster_service.generate_colormap_overlay(
            ndwi_arr, cmap_name="Blues", vmin=-0.5, vmax=0.5
        )
        return Response(content=png_bytes, media_type="image/png", headers={
            "X-Bounds": str(bounds_data.get("bounds", [])),
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)


@router.get("/{project_id}/ndvi-bounds")
async def get_ndvi_bounds(project_id: int, object_name: str):
    """Return the geographic bounds for an input GeoTIFF (for heatmap overlay positioning)."""
    local_path = f"/tmp/bounds_ndvi_{object_name.replace('/', '_')}"
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


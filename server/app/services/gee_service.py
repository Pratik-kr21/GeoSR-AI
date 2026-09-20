import ee
import os
import uuid
import requests
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.services.storage_service import storage_service
from app.services.raster_service import raster_service
from app.config import settings

logger = logging.getLogger(__name__)

class GEEService:
    def __init__(self):
        self.is_initialized = False

    def initialize(self):
        if self.is_initialized:
            return True
            
        key_path = settings.GEE_CREDENTIALS_PATH
        
        if not key_path or not os.path.exists(key_path):
            logger.warning(f"GEE Setup Warning: Credentials not found at {key_path}. Earth Engine features will be disabled.")
            return False
            
        try:
            with open(key_path, 'r') as f:
                key_data = json.load(f)
                
            credentials = ee.ServiceAccountCredentials(
                key_data.get("client_email", settings.GEE_SERVICE_ACCOUNT_EMAIL), 
                key_file=key_path
            )
            ee.Initialize(credentials, project=settings.GEE_PROJECT_ID or key_data.get("project_id"))
            self.is_initialized = True
            logger.info("Successfully connected to Google Earth Engine!")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Earth Engine: {e}")
            return False

    def fetch_cloud_masked_composite(
        self,
        project_id: int,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        buffer_km: Optional[float] = 5.0,
        bbox: Optional[List[float]] = None,
        days_back: int = 30,
        scene_cloud_threshold: int = 60,
    ) -> Dict[str, Any]:
        """
        Fetches a cloud-masked composite from Sentinel-2 Harmonized Surface Reflectance.
        """
        if not self.initialize():
            return {"error": "Google Earth Engine is not configured."}
            
        try:
            if bbox is None:
                if lat is None or lon is None:
                    raise ValueError("Must provide either a bounding box (bbox) or lat/lon center point.")
                lat_diff = buffer_km / 111.0
                lon_diff = buffer_km / (111.0 * math.cos(math.radians(lat)))
                bbox = [lon - lon_diff, lat - lat_diff, lon + lon_diff, lat + lat_diff]

            west, south, east, north = bbox
            region = ee.Geometry.Rectangle([west, south, east, north])
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # SCL band (Scene Classification Layer) values for S2:
            # 4: Vegetation, 5: Not-vegetated, 6: Water, 7: Unclassified, 8: Cloud medium prob, 9: Cloud high prob, 10: Thin cirrus, 11: Snow/ice
            # We want to mask out clouds (8, 9, 10), shadows (3) and invalid pixels (0, 1, 2)
            
            def mask_clouds_and_shadows(image):
                scl = image.select('SCL')
                # Keep valid pixels: 4 (veg), 5 (non-veg), 6 (water), 7 (unclassified), 11 (snow)
                # You could also use a simpler approach masking just 3,8,9,10. Let's keep 4,5,6,7,11
                mask = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7)).Or(scl.eq(11))
                return image.updateMask(mask)

            collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(region)
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', scene_cloud_threshold)))
                
            count = collection.size().getInfo()
            if count == 0:
                return {"error": f"No scenes found under {scene_cloud_threshold}% cloud cover in the last {days_back} days."}
                
            # Apply cloud mask and median composite
            masked_collection = collection.map(mask_clouds_and_shadows)
            composite = masked_collection.median()
            
            # Select bands and reorder (B, G, R, NIR)
            image_4band = composite.select(['B2', 'B3', 'B4', 'B8'])
            
            # Calculate valid pixel coverage
            # We check how many pixels have valid data in B2
            valid_mask = image_4band.select('B2').mask()
            
            # Download URL for the composite
            url = image_4band.getDownloadURL({
                'scale': 10,
                'crs': 'EPSG:4326',
                'region': region,
                'format': 'GEO_TIFF'
            })
            
            # Also fetch valid coverage stat
            # Compute fraction of valid pixels in region
            area_valid = valid_mask.multiply(ee.Image.pixelArea()).reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=region,
                scale=10,
                maxPixels=1e9
            ).get('B2').getInfo()
            
            area_total = ee.Image.pixelArea().reduceRegion(
                reducer=ee.Reducer.sum(),
                geometry=region,
                scale=10,
                maxPixels=1e9
            ).get('area').getInfo()
            
            valid_pixel_percentage = (area_valid / area_total * 100) if area_total else 0

            # Download GeoTIFF
            file_id = str(uuid.uuid4())
            filename = f"gee_composite_{end_date.strftime('%Y%m%d')}.tif"
            temp_file_path = f"/tmp/{file_id}_{filename}"
            
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                return {"error": f"Failed to download GeoTIFF from GEE URL: HTTP {response.status_code}"}
                
            with open(temp_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            # Upload to MinIO
            object_name = f"projects/{project_id}/inputs/{file_id}_{filename}"
            storage_service.upload_file(temp_file_path, object_name)
            os.remove(temp_file_path)
            
            warnings = []
            if valid_pixel_percentage < 50:
                warnings.append(f"Low valid pixel coverage ({valid_pixel_percentage:.1f}%). Composite may have gaps.")
            
            return {
                "status": "success",
                "file_id": file_id,
                "filename": filename,
                "object_name": object_name,
                "date_range": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                "scene_count": count,
                "valid_pixel_percentage": valid_pixel_percentage,
                "warnings": warnings,
                "bounds": bbox
            }
            
        except Exception as e:
            logger.error(f"GEE fetch_cloud_masked_composite error: {e}")
            return {"error": str(e)}

gee_service = GEEService()

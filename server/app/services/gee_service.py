import ee
import os
import uuid
import requests
import json
from datetime import datetime, timedelta
from app.services.storage_service import storage_service
from app.services.raster_service import raster_service

class GEEService:
    def __init__(self):
        self.is_initialized = False

    def initialize(self):
        if self.is_initialized:
            return True
            
        # For the hackathon, we assume the user has placed their Service Account JSON in the backend root
        # named "gee_key.json"
        key_path = "/app/gee_key.json"
        
        if not os.path.exists(key_path):
            print("GEE Setup Warning: gee_key.json not found. Earth Engine features will be disabled.")
            return False
            
        try:
            with open(key_path, 'r') as f:
                key_data = json.load(f)
                
            credentials = ee.ServiceAccountCredentials(
                key_data.get("client_email"), 
                key_file=key_path
            )
            ee.Initialize(credentials)
            self.is_initialized = True
            print("Successfully connected to Google Earth Engine!")
            return True
        except Exception as e:
            print(f"Failed to initialize Earth Engine: {e}")
            return False

    def fetch_live_imagery(self, project_id: int, bbox: list[float], max_cloud_cover: int = 20) -> dict:
        """
        Fetches the latest Sentinel-2 imagery for a given bounding box [west, south, east, north]
        """
        if not self.initialize():
            return {"error": "Google Earth Engine is not configured (missing or invalid gee_key.json)."}
            
        try:
            west, south, east, north = bbox
            region = ee.Geometry.Rectangle([west, south, east, north])
            
            # Fetch the last 3 months of data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)
            
            # Sentinel-2 Harmonized Surface Reflectance
            collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                .filterBounds(region)
                .filterDate(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', max_cloud_cover))
                .sort('system:time_start', False)) # Most recent first
                
            # Check if any images match
            count = collection.size().getInfo()
            if count == 0:
                return {"error": "No cloud-free imagery found for this region in the last 90 days."}
                
            # Get the most recent image
            image = ee.Image(collection.first())
            
            # Select the 4 bands we need: Blue(B2), Green(B3), Red(B4), NIR(B8)
            # Reorder them to match our expected stack (B, G, R, NIR)
            image_4band = image.select(['B2', 'B3', 'B4', 'B8'])
            
            # Export the image to a download URL (limit resolution to 10m/pixel to match S2)
            # Using getDownloadURL generates a direct link to a GeoTIFF
            url = image_4band.getDownloadURL({
                'scale': 10,
                'crs': 'EPSG:4326',
                'region': region,
                'format': 'GEO_TIFF'
            })
            
            print(f"GEE Download URL generated: {url}")
            
            # Download the GeoTIFF to a temporary file
            file_id = str(uuid.uuid4())
            filename = f"gee_{end_date.strftime('%Y%m%d')}.tif"
            temp_file_path = f"/tmp/{file_id}_{filename}"
            
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                return {"error": f"Failed to download GeoTIFF from GEE URL: HTTP {response.status_code}"}
                
            with open(temp_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            # Verify the downloaded file
            metadata = raster_service.read_metadata(temp_file_path)
            if "error" in metadata:
                os.remove(temp_file_path)
                return {"error": f"Downloaded file is not a valid GeoTIFF: {metadata['error']}"}
                
            # Upload to our MinIO storage
            object_name = f"projects/{project_id}/inputs/{file_id}_{filename}"
            storage_service.upload_file(temp_file_path, object_name)
            
            # Cleanup
            os.remove(temp_file_path)
            
            return {
                "status": "success",
                "file_id": file_id,
                "filename": filename,
                "object_name": object_name
            }
            
        except Exception as e:
            return {"error": str(e)}

gee_service = GEEService()

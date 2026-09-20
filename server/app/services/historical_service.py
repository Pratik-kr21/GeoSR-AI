import ee
import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
import math
import requests
from app.services.storage_service import storage_service
from app.services.gee_service import gee_service

class HistoricalService:
    def __init__(self):
        pass
        
    def _get_landsat_collection(self, year: int):
        if year < 1999:
            return 'LANDSAT/LT05/C02/T1_L2', 'SR_B3', 'SR_B4' # Red, NIR for L5
        elif year < 2013:
            return 'LANDSAT/LE07/C02/T1_L2', 'SR_B3', 'SR_B4' # Red, NIR for L7
        elif year < 2021:
            return 'LANDSAT/LC08/C02/T1_L2', 'SR_B4', 'SR_B5' # Red, NIR for L8
        else:
            return 'LANDSAT/LC09/C02/T1_L2', 'SR_B4', 'SR_B5' # Red, NIR for L9
            
    def analyze_historical_ndvi(
        self,
        project_id: int,
        lat: float,
        lon: float,
        buffer_km: float,
        years: List[int],
        season_start: str,
        season_end: str,
        max_cloud_cover: int = 40
    ) -> Dict[str, Any]:
        if not gee_service.initialize():
            return {"error": "Google Earth Engine is not configured."}
            
        lat_diff = buffer_km / 111.0
        lon_diff = buffer_km / (111.0 * math.cos(math.radians(lat)))
        bbox = [lon - lon_diff, lat - lat_diff, lon + lon_diff, lat + lat_diff]
        region = ee.Geometry.Rectangle(bbox)
        
        results = []
        
        for year in years:
            try:
                collection_name, red_band, nir_band = self._get_landsat_collection(year)
                
                # Cloud masking function for Landsat Collection 2 SR
                def mask_l2_clouds(image):
                    qa = image.select('QA_PIXEL')
                    cloud_shadow_bitmask = (1 << 4)
                    clouds_bitmask = (1 << 3)
                    mask = qa.bitwiseAnd(cloud_shadow_bitmask).eq(0).And(qa.bitwiseAnd(clouds_bitmask).eq(0))
                    
                    # Apply scaling factors for Collection 2 Surface Reflectance
                    optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
                    return image.addBands(optical_bands, None, True).updateMask(mask)
                    
                start_date = f"{year}-{season_start}"
                end_date = f"{year}-{season_end}"
                
                collection = (ee.ImageCollection(collection_name)
                    .filterBounds(region)
                    .filterDate(start_date, end_date)
                    .filter(ee.Filter.lt('CLOUD_COVER', max_cloud_cover))
                    .map(mask_l2_clouds))
                    
                count = collection.size().getInfo()
                if count == 0:
                    results.append({
                        "year": year,
                        "error": "No scenes available",
                        "mission": collection_name.split('/')[1]
                    })
                    continue
                    
                median_composite = collection.median()
                ndvi = median_composite.normalizedDifference([nir_band, red_band]).rename('NDVI')
                
                # Calculate stats
                stats = ndvi.reduceRegion(
                    reducer=ee.Reducer.mean().combine(
                        reducer2=ee.Reducer.median(), sharedInputs=True
                    ).combine(
                        reducer2=ee.Reducer.stdDev(), sharedInputs=True
                    ).combine(
                        reducer2=ee.Reducer.percentile([10, 25, 75, 90]), sharedInputs=True
                    ),
                    geometry=region,
                    scale=30,
                    maxPixels=1e9
                ).getInfo()
                
                # Calculate valid pixels count vs total for the bounding box
                valid_mask = ndvi.mask()
                area_valid = valid_mask.multiply(ee.Image.pixelArea()).reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=region,
                    scale=30,
                    maxPixels=1e9
                ).get('NDVI').getInfo()
                
                area_total = ee.Image.pixelArea().reduceRegion(
                    reducer=ee.Reducer.sum(),
                    geometry=region,
                    scale=30,
                    maxPixels=1e9
                ).get('area').getInfo()
                
                valid_pixel_percentage = (area_valid / area_total * 100) if area_total else 0
                
                # Thumbnail
                thumb_url = ndvi.getThumbURL({
                    'min': -0.1,
                    'max': 0.8,
                    'palette': ['red', 'yellow', 'green', 'darkgreen'],
                    'region': region,
                    'dimensions': 256
                })
                
                thumb_path = f"/tmp/{uuid.uuid4()}_ndvi_{year}.png"
                resp = requests.get(thumb_url)
                if resp.status_code == 200:
                    with open(thumb_path, 'wb') as f:
                        f.write(resp.content)
                    object_name = f"projects/{project_id}/outputs/historical_{year}.png"
                    storage_service.upload_file(thumb_path, object_name)
                    os.remove(thumb_path)
                else:
                    object_name = None
                    
                warnings = []
                if year >= 2003 and collection_name == 'LANDSAT/LE07/C02/T1_L2':
                    warnings.append("Landsat 7 Scan Line Corrector failure affects this year (striping visible).")
                    
                results.append({
                    "year": year,
                    "mission": collection_name.split('/')[1],
                    "scene_count": count,
                    "valid_pixel_percentage": valid_pixel_percentage,
                    "ndvi_mean": stats.get('NDVI_mean'),
                    "ndvi_median": stats.get('NDVI_median'),
                    "ndvi_std": stats.get('NDVI_stdDev'),
                    "ndvi_p10": stats.get('NDVI_p10'),
                    "ndvi_p25": stats.get('NDVI_p25'),
                    "ndvi_p75": stats.get('NDVI_p75'),
                    "ndvi_p90": stats.get('NDVI_p90'),
                    "thumbnail": object_name,
                    "warnings": warnings
                })
                
            except Exception as e:
                results.append({
                    "year": year,
                    "error": str(e)
                })
                
        return {
            "status": "completed",
            "results": results,
            "season_start": season_start,
            "season_end": season_end,
            "warnings": ["Cross-sensor NDVI comparisons require careful calibration adjustments."]
        }

historical_service = HistoricalService()

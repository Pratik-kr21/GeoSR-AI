import numpy as np
import rasterio
from typing import Dict, Any

class TerrainService:
    """
    Service for Copernicus DEM elevation processing.
    """
    
    def compute_elevation_stats(self, dem_path: str) -> Dict[str, Any]:
        with rasterio.open(dem_path) as src:
            dem = src.read(1)
            mask = src.read(2)
            
        valid_mask = mask > 0.5
        valid_pixels = np.count_nonzero(valid_mask)
        total_pixels = mask.size
        valid_percentage = (valid_pixels / total_pixels * 100) if total_pixels > 0 else 0
        
        if valid_pixels == 0:
            return {"valid_percentage": 0.0}
            
        dem_valid = dem[valid_mask]
        
        # Calculate histogram bins for frontend visualization
        hist, bin_edges = np.histogram(dem_valid, bins=20)
        
        return {
            "min_elevation": float(np.min(dem_valid)),
            "max_elevation": float(np.max(dem_valid)),
            "mean_elevation": float(np.mean(dem_valid)),
            "median_elevation": float(np.median(dem_valid)),
            "std_elevation": float(np.std(dem_valid)),
            "valid_percentage": round(valid_percentage, 2),
            "histogram": {
                "counts": hist.tolist(),
                "bins": bin_edges.tolist()
            }
        }
        
    def compute_slope(self, dem_path: str) -> Dict[str, Any]:
        """
        Calculate slope using real pixel dimensions in metric terms (approximate if in degrees).
        """
        with rasterio.open(dem_path) as src:
            dem = src.read(1)
            mask = src.read(2)
            transform = src.transform
            
        valid_mask = mask > 0.5
        valid_pixels = np.count_nonzero(valid_mask)
        
        if valid_pixels == 0:
            return {"mean_slope": 0, "max_slope": 0, "steep_area_fraction": 0}
            
        # Very rough conversion of pixel dimensions from degrees to meters if CRS is WGS84
        # Assuming ~111,320 meters per degree at the equator
        res_x_deg = transform.a
        res_y_deg = -transform.e
        
        res_x_m = res_x_deg * 111320
        res_y_m = res_y_deg * 111320
        
        # Using numpy gradient to calculate slopes in X and Y directions
        dy, dx = np.gradient(dem, res_y_m, res_x_m)
        slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
        slope_deg = np.degrees(slope_rad)
        
        slope_valid = slope_deg[valid_mask]
        
        steep_threshold_deg = 20.0 # arbitrary threshold for steep slope
        steep_pixels = np.count_nonzero(slope_valid > steep_threshold_deg)
        
        return {
            "mean_slope": float(np.mean(slope_valid)),
            "max_slope": float(np.max(slope_valid)),
            "steep_area_fraction": steep_pixels / valid_pixels
        }
        
    def compute_low_lying_fraction(self, dem_path: str, percentile: float = 20.0) -> Dict[str, Any]:
        """
        Calculates fraction of area lying below the given percentile of elevation.
        Returns elevation threshold, low-lying fraction, low-lying area.
        """
        with rasterio.open(dem_path) as src:
            dem = src.read(1)
            mask = src.read(2)
            transform = src.transform
            
        valid_mask = mask > 0.5
        valid_pixels = np.count_nonzero(valid_mask)
        
        if valid_pixels == 0:
            return {"elevation_threshold": 0, "low_lying_fraction": 0, "low_lying_area_km2": 0}
            
        dem_valid = dem[valid_mask]
        threshold = float(np.percentile(dem_valid, percentile))
        
        low_lying_mask = (dem <= threshold) & valid_mask
        low_lying_pixels = np.count_nonzero(low_lying_mask)
        
        # Pixel area in sq km
        pixel_width_deg = transform.a
        pixel_height_deg = -transform.e
        pixel_area_km2 = (pixel_width_deg * 111) * (pixel_height_deg * 111)
        
        low_lying_area_km2 = low_lying_pixels * pixel_area_km2
        low_lying_fraction = low_lying_pixels / valid_pixels
        
        return {
            "elevation_threshold": threshold,
            "low_lying_fraction": round(low_lying_fraction, 4),
            "low_lying_area_km2": round(low_lying_area_km2, 2)
        }

terrain_service = TerrainService()

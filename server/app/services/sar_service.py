import numpy as np
import rasterio
from typing import Dict, Any, Optional

class SARService:
    """
    Service for Sentinel-1 SAR analysis.
    """
    
    def analyze_sar_scene(
        self,
        scene_path: str,
        threshold_db: float = -15.0,
        baseline_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a SAR scene (VV, VH, mask bands).
        Returns VV/VH stats, valid pixel %, potential water fraction/area, etc.
        """
        with rasterio.open(scene_path) as src:
            # We expect 3 bands from our evalscript: VV, VH, dataMask
            if src.count < 3:
                raise ValueError("Expected at least 3 bands (VV, VH, mask).")
            vv = src.read(1)
            vh = src.read(2)
            mask = src.read(3)
            
            transform = src.transform
            
        # Valid pixels
        valid_mask = mask > 0.5
        total_pixels = mask.size
        valid_pixels = np.count_nonzero(valid_mask)
        valid_percentage = (valid_pixels / total_pixels * 100) if total_pixels > 0 else 0
        
        if valid_pixels == 0:
            return {
                "valid_percentage": 0.0,
                "warnings": ["No valid pixels found in SAR scene."]
            }
            
        # Convert VV and VH from linear power to decibels
        # Suppress divide by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            vv_db = 10 * np.log10(vv)
            vh_db = 10 * np.log10(vh)
            
        vv_valid = vv_db[valid_mask & np.isfinite(vv_db)]
        vh_valid = vh_db[valid_mask & np.isfinite(vh_db)]
        
        vv_mean = float(np.mean(vv_valid)) if len(vv_valid) > 0 else None
        vv_median = float(np.median(vv_valid)) if len(vv_valid) > 0 else None
        vv_std = float(np.std(vv_valid)) if len(vv_valid) > 0 else None
        
        vh_mean = float(np.mean(vh_valid)) if len(vh_valid) > 0 else None
        vh_median = float(np.median(vh_valid)) if len(vh_valid) > 0 else None
        vh_std = float(np.std(vh_valid)) if len(vh_valid) > 0 else None
        
        # Potential water mask (VV < threshold_db)
        potential_water_mask = (vv_db < threshold_db) & valid_mask
        potential_water_pixels = np.count_nonzero(potential_water_mask)
        potential_water_fraction = potential_water_pixels / valid_pixels if valid_pixels > 0 else 0
        
        # Calculate pixel area in square kilometres
        pixel_width_deg = transform.a
        pixel_height_deg = -transform.e
        # Rough conversion to km at equator: 1 deg = 111 km
        pixel_area_km2 = (pixel_width_deg * 111) * (pixel_height_deg * 111)
        potential_water_area_km2 = potential_water_pixels * pixel_area_km2
        
        results = {
            "valid_percentage": round(valid_percentage, 2),
            "vv_mean": round(vv_mean, 2) if vv_mean else None,
            "vv_median": round(vv_median, 2) if vv_median else None,
            "vv_std": round(vv_std, 2) if vv_std else None,
            "vh_mean": round(vh_mean, 2) if vh_mean else None,
            "vh_median": round(vh_median, 2) if vh_median else None,
            "vh_std": round(vh_std, 2) if vh_std else None,
            "potential_water_fraction": round(potential_water_fraction, 4),
            "potential_water_area_km2": round(potential_water_area_km2, 2),
            "confidence": "Low",  # Without baseline it's just a candidate
            "warnings": ["Low backscatter does not confirm flooding without temporal baseline comparison."]
        }
        
        # Temporal analysis if baseline is provided
        if baseline_path:
            try:
                with rasterio.open(baseline_path) as src_base:
                    vv_base = src_base.read(1)
                    mask_base = src_base.read(3)
                
                valid_base = mask_base > 0.5
                with np.errstate(divide='ignore', invalid='ignore'):
                    vv_base_db = 10 * np.log10(vv_base)
                    
                # New water candidate: was NOT water before, is water now
                # Say, baseline VV > -12 dB (not water) and current VV < -15 dB (water)
                new_water_mask = (vv_base_db > (threshold_db + 3)) & potential_water_mask & valid_base
                new_water_pixels = np.count_nonzero(new_water_mask)
                new_water_area_km2 = new_water_pixels * pixel_area_km2
                
                results["new_potential_water_area_km2"] = round(new_water_area_km2, 2)
                results["new_water_fraction"] = new_water_pixels / valid_pixels
                results["confidence"] = "Medium" # Increased confidence with baseline
                results["warnings"].append("Baseline comparison completed successfully.")
            except Exception as e:
                results["warnings"].append(f"Baseline comparison failed: {str(e)}")
                
        return results

sar_service = SARService()

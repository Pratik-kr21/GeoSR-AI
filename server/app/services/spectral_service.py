import rasterio
import numpy as np
from typing import Optional, Dict, Any, Tuple

from app.services.raster_service import raster_service
from app.services.storage_service import storage_service

# ─── Configurable Thresholds ───────────────────────────────────────────────────

NDVI_THRESHOLDS = {
    "very_low":  (-1.0, 0.2,  "Very Low Vegetation / Bare Soil"),
    "low":       (0.2,  0.4,  "Low Vegetation"),
    "moderate":  (0.4,  0.6,  "Moderate Vegetation"),
    "healthy":   (0.6,  0.8,  "Healthy Vegetation"),
    "very_healthy": (0.8, 1.0, "Very Healthy / Dense Vegetation"),
}

NDWI_THRESHOLDS = {
    "very_dry":  (-1.0, -0.3, "Very Low Water Content / Drought Stress"),
    "dry":       (-0.3, 0.0,  "Low Water Presence"),
    "moderate":  (0.0,  0.2,  "Moderate Water Presence"),
    "wet":       (0.2,  0.5,  "High Water Presence"),
    "water":     (0.5,  1.0,  "Open Water Body Detected"),
}


def _classify_value(value: float, thresholds: dict) -> str:
    """Classify a scalar value against a threshold dict."""
    for name, (lo, hi, label) in thresholds.items():
        if lo <= value < hi:
            return label
    return "Unknown"


def _download_local(object_name: str, suffix: str) -> str:
    """Download from MinIO to a temp local path."""
    import os
    local = f"/tmp/spectral_{suffix}_{object_name.replace('/', '_')}"
    storage_service.download_file(object_name, local)
    return local


def _cleanup(path: str):
    import os
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


class SpectralService:
    """
    Computes NDVI and NDWI analytics from raw Sentinel-2 GeoTIFF files.

    Uses the ORIGINAL satellite data, not the SRCNN-enhanced output,
    to ensure scientific validity of spectral measurements.
    """

    def compute_spectral_indices(self, object_name: str) -> Dict[str, Any]:
        """
        Main entry point. Downloads file from MinIO, auto-detects bands,
        computes NDVI and NDWI, returns stats dict.

        Returns:
            dict with keys: ndvi_*, ndwi_*, band_mapping_used, band_mapping_warning, ndvi_array, ndwi_array
        """
        import os
        local_path = None
        try:
            local_path = _download_local(object_name, "si")

            # Detect bands
            band_info = raster_service.detect_sentinel2_bands(local_path)
            warning = band_info.pop("warning", None)

            result = {
                "band_mapping_used": band_info,
                "band_mapping_warning": warning,
                "ndvi_available": "yes",
                "ndwi_available": "yes",
                "ndvi_array": None,
                "ndwi_array": None,
            }

            with rasterio.open(local_path) as src:
                def read_band(key) -> Optional[np.ndarray]:
                    idx = band_info.get(key)
                    if idx is None:
                        return None
                    raw = src.read(idx).astype(np.float32)
                    # Normalize to [0,1] regardless of input bit depth
                    nodata = src.nodata
                    if nodata is not None:
                        raw = np.where(raw == nodata, np.nan, raw)
                    if raw.dtype == np.float32 and np.nanmax(raw) > 1.0:
                        max_val = 65535.0 if np.nanmax(raw) > 255 else 255.0
                        raw = raw / max_val
                    return raw

                red = read_band("red")
                nir = read_band("nir")
                green = read_band("green")

                # ── NDVI ──────────────────────────────────────────────────
                if red is not None and nir is not None:
                    denom = nir + red
                    ndvi = np.where(denom == 0, np.nan, (nir - red) / denom)
                    valid = ndvi[~np.isnan(ndvi)]
                    if len(valid) > 0:
                        result.update({
                            "ndvi_mean":  float(np.nanmean(ndvi)),
                            "ndvi_min":   float(np.nanmin(ndvi)),
                            "ndvi_max":   float(np.nanmax(ndvi)),
                            "ndvi_std":   float(np.nanstd(ndvi)),
                            "ndvi_p10":   float(np.nanpercentile(ndvi, 10)),
                            "ndvi_p25":   float(np.nanpercentile(ndvi, 25)),
                            "ndvi_p75":   float(np.nanpercentile(ndvi, 75)),
                            "ndvi_p90":   float(np.nanpercentile(ndvi, 90)),
                            "ndvi_health_class": _classify_value(float(np.nanmean(ndvi)), NDVI_THRESHOLDS),
                            "ndvi_array": ndvi,
                        })
                    else:
                        result["ndvi_available"] = "no: all pixels are NoData"
                else:
                    missing = []
                    if red is None: missing.append("Red (B04)")
                    if nir is None: missing.append("NIR (B08)")
                    result["ndvi_available"] = f"no: required bands missing — {', '.join(missing)}"

                # ── NDWI ──────────────────────────────────────────────────
                if green is not None and nir is not None:
                    denom = green + nir
                    ndwi = np.where(denom == 0, np.nan, (green - nir) / denom)
                    valid = ndwi[~np.isnan(ndwi)]
                    if len(valid) > 0:
                        result.update({
                            "ndwi_mean":  float(np.nanmean(ndwi)),
                            "ndwi_min":   float(np.nanmin(ndwi)),
                            "ndwi_max":   float(np.nanmax(ndwi)),
                            "ndwi_std":   float(np.nanstd(ndwi)),
                            "ndwi_water_class": _classify_value(float(np.nanmean(ndwi)), NDWI_THRESHOLDS),
                            "ndwi_array": ndwi,
                        })
                    else:
                        result["ndwi_available"] = "no: all pixels are NoData"
                else:
                    missing = []
                    if green is None: missing.append("Green (B03)")
                    if nir is None: missing.append("NIR (B08)")
                    result["ndwi_available"] = f"no: required bands missing — {', '.join(missing)}"

            return result

        finally:
            _cleanup(local_path)

    def get_extra_stats(self, ndvi_array: Optional[np.ndarray], ndwi_array: Optional[np.ndarray]) -> dict:
        """Compute additional histogram / percentile stats."""
        stats = {}
        if ndvi_array is not None:
            valid = ndvi_array[~np.isnan(ndvi_array)]
            if len(valid):
                # Distribution buckets for histogram sparkline
                counts, edges = np.histogram(valid, bins=10, range=(-1, 1))
                stats["ndvi_histogram"] = {
                    "counts": counts.tolist(),
                    "edges": [round(float(e), 2) for e in edges.tolist()],
                }
        if ndwi_array is not None:
            valid = ndwi_array[~np.isnan(ndwi_array)]
            if len(valid):
                counts, edges = np.histogram(valid, bins=10, range=(-1, 1))
                stats["ndwi_histogram"] = {
                    "counts": counts.tolist(),
                    "edges": [round(float(e), 2) for e in edges.tolist()],
                }
        return stats


spectral_service = SpectralService()

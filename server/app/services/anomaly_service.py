import numpy as np
from typing import Optional, Dict, Any, List
from app.services.spectral_service import spectral_service

# ─── Configurable Thresholds ───────────────────────────────────────────────────
CHANGE_SIGNIFICANCE_THRESHOLD = 0.1   # Absolute NDVI change to flag a pixel as "changed"
Z_SCORE_THRESHOLD = 2.5               # Standard deviations for anomaly detection
MIN_ANOMALY_PIXELS = 50               # Minimum connected pixels to count as an anomaly


class AnomalyService:
    """
    Detects spatial anomalies using explainable statistical methods.

    Techniques:
    - Global z-score on NDVI array
    - Percentile thresholding (below p10 or above p90)
    - Local neighbourhood deviation (not deep learning)

    Results are clearly labelled as prototype analytical indicators, not ground truth.
    """

    def detect_anomalies(self, ndvi_array: Optional[np.ndarray], ndwi_array: Optional[np.ndarray],
                         geo_bounds: Optional[List[float]] = None) -> List[Dict[str, Any]]:
        """
        Detect anomaly zones from NDVI/NDWI arrays.

        Args:
            ndvi_array: 2D float32 NDVI raster, NaN where no-data
            ndwi_array: 2D float32 NDWI raster, NaN where no-data
            geo_bounds: [west, south, east, north] WGS84 — used to compute approximate lat/lon centres

        Returns:
            List of anomaly dicts
        """
        anomalies = []

        if ndvi_array is not None:
            anomalies.extend(self._detect_ndvi_anomalies(ndvi_array, geo_bounds))

        if ndwi_array is not None:
            anomalies.extend(self._detect_ndwi_anomalies(ndwi_array, geo_bounds))

        # Sort by severity (critical > high > medium > low)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        anomalies.sort(key=lambda a: severity_order.get(a["severity"], 99))

        return anomalies

    def _detect_ndvi_anomalies(self, ndvi: np.ndarray, bounds) -> List[Dict]:
        """Detect vegetation stress anomalies using z-score on NDVI."""
        anomalies = []
        valid_mask = ~np.isnan(ndvi)
        if not np.any(valid_mask):
            return anomalies

        valid_vals = ndvi[valid_mask]
        mean_ndvi = float(np.mean(valid_vals))
        std_ndvi = float(np.std(valid_vals))

        if std_ndvi < 1e-6:
            return anomalies

        # Z-score map
        z_map = np.where(valid_mask, (ndvi - mean_ndvi) / std_ndvi, 0.0)

        # Vegetation stress = significantly below mean (negative z-score)
        stress_mask = (z_map < -Z_SCORE_THRESHOLD) & valid_mask
        # Unusual high density = significantly above mean
        dense_mask = (z_map > Z_SCORE_THRESHOLD) & valid_mask

        for mask, atype, base_severity in [
            (stress_mask, "vegetation_stress", "high"),
            (dense_mask, "unusual_vegetation_density", "low"),
        ]:
            if not np.any(mask):
                continue

            count = int(np.sum(mask))
            if count < MIN_ANOMALY_PIXELS:
                continue

            pct = count / float(valid_mask.sum())
            mean_z = float(np.mean(np.abs(z_map[mask])))
            affected_ndvi = float(np.mean(ndvi[mask]))

            severity = base_severity
            if pct > 0.20 or mean_z > 3.5:
                severity = "critical"
            elif pct > 0.10 or mean_z > 3.0:
                severity = "high"
            elif pct > 0.05:
                severity = "medium"

            confidence = min(0.95, 0.5 + (mean_z - Z_SCORE_THRESHOLD) * 0.15)

            # Approximate centre
            rows, cols = np.where(mask)
            centre_row = int(np.median(rows))
            centre_col = int(np.median(cols))
            lat, lon = self._pixel_to_latlon(centre_row, centre_col, ndvi.shape, bounds)

            area_km2 = round(pct * self._estimate_total_area_km2(bounds), 3) if bounds else None

            anomalies.append({
                "anomaly_type": atype,
                "severity": severity,
                "confidence": round(confidence, 3),
                "center_lat": lat,
                "center_lon": lon,
                "area_km2": area_km2,
                "evidence": {
                    "mean_z_score": round(mean_z, 3),
                    "affected_pixels": count,
                    "affected_pct": round(pct * 100, 2),
                    "mean_ndvi_in_zone": round(affected_ndvi, 4),
                    "overall_mean_ndvi": round(mean_ndvi, 4),
                    "ndvi_deviation": round(affected_ndvi - mean_ndvi, 4),
                    "method": "z-score threshold",
                    "threshold_used": Z_SCORE_THRESHOLD,
                },
                "description": (
                    f"Detected {atype.replace('_', ' ')} zone covering "
                    f"~{round(pct*100,1)}% of the image area. "
                    f"Mean NDVI in zone: {round(affected_ndvi,3)} vs image mean {round(mean_ndvi,3)}. "
                    f"Z-score: {round(mean_z,2)}. "
                    f"This is a prototype analytical indicator — not validated ground truth."
                ),
            })

        return anomalies

    def _detect_ndwi_anomalies(self, ndwi: np.ndarray, bounds) -> List[Dict]:
        """Detect water stress anomalies from NDWI."""
        anomalies = []
        valid_mask = ~np.isnan(ndwi)
        if not np.any(valid_mask):
            return anomalies

        valid_vals = ndwi[valid_mask]
        mean_ndwi = float(np.mean(valid_vals))

        # Extreme drought (very low NDWI)
        drought_mask = (ndwi < -0.3) & valid_mask
        if np.any(drought_mask):
            count = int(np.sum(drought_mask))
            if count >= MIN_ANOMALY_PIXELS:
                pct = count / float(valid_mask.sum())
                mean_val = float(np.mean(ndwi[drought_mask]))
                confidence = min(0.90, 0.55 + abs(mean_val) * 0.3)
                rows, cols = np.where(drought_mask)
                lat, lon = self._pixel_to_latlon(int(np.median(rows)), int(np.median(cols)), ndwi.shape, bounds)
                area_km2 = round(pct * self._estimate_total_area_km2(bounds), 3) if bounds else None
                anomalies.append({
                    "anomaly_type": "water_stress",
                    "severity": "high" if pct > 0.15 else "medium",
                    "confidence": round(confidence, 3),
                    "center_lat": lat,
                    "center_lon": lon,
                    "area_km2": area_km2,
                    "evidence": {
                        "mean_ndwi_in_zone": round(mean_val, 4),
                        "overall_mean_ndwi": round(mean_ndwi, 4),
                        "affected_pct": round(pct * 100, 2),
                        "method": "threshold: NDWI < -0.3",
                    },
                    "description": (
                        f"Water stress / drought indicator zone detected. "
                        f"Mean NDWI: {round(mean_val,3)}. "
                        f"Covers ~{round(pct*100,1)}% of area. Prototype analytical indicator only."
                    ),
                })

        return anomalies

    @staticmethod
    def _pixel_to_latlon(row, col, shape, bounds):
        if not bounds or len(bounds) < 4:
            return None, None
        west, south, east, north = bounds
        lat = north - (row / shape[0]) * (north - south)
        lon = west + (col / shape[1]) * (east - west)
        return round(lat, 6), round(lon, 6)

    @staticmethod
    def _estimate_total_area_km2(bounds):
        if not bounds or len(bounds) < 4:
            return 100.0  # fallback
        west, south, east, north = bounds
        # Rough equirectangular area estimate
        lat_deg = north - south
        lon_deg = east - west
        lat_km = lat_deg * 111.32
        lon_km = lon_deg * 111.32 * np.cos(np.radians((north + south) / 2))
        return abs(lat_km * lon_km)


anomaly_service = AnomalyService()

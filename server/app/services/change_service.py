import numpy as np
from typing import Optional, Dict, Any, List
from app.services.spectral_service import spectral_service

# ─── Configurable ─────────────────────────────────────────────────────────────
CHANGE_SIGNIFICANCE_THRESHOLD = 0.1   # min |NDVI diff| to flag pixel as changed


class ChangeService:
    """
    Temporal change detection between two satellite observations.

    Uses original Sentinel-2 NDVI/NDWI, never SRCNN output.
    All outputs are labelled as prototype analytical indicators.
    """

    def compare_observations(
        self,
        before_object_name: str,
        after_object_name: str,
        project_location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compare two GeoTIFF observations and return change statistics.

        Returns:
            dict with change metrics, categories, hotspots, confidence, summary
        """
        # Compute spectral indices for both observations
        before = spectral_service.compute_spectral_indices(before_object_name)
        after = spectral_service.compute_spectral_indices(after_object_name)

        result = {
            "before_ndvi_mean": before.get("ndvi_mean"),
            "after_ndvi_mean":  after.get("ndvi_mean"),
            "before_ndwi_mean": before.get("ndwi_mean"),
            "after_ndwi_mean":  after.get("ndwi_mean"),
            "ndvi_change": None,
            "ndwi_change": None,
            "change_percentage": None,
            "changed_area_km2": None,
            "change_type": "unknown",
            "change_categories": [],
            "hotspots": [],
            "confidence": 0.5,
            "summary": "Insufficient data for change detection.",
        }

        # ── NDVI change ───────────────────────────────────────────────────────
        before_ndvi = before.get("ndvi_mean")
        after_ndvi = after.get("ndvi_mean")
        before_arr = before.get("ndvi_array")
        after_arr = after.get("ndvi_array")

        if before_ndvi is not None and after_ndvi is not None:
            ndvi_change = after_ndvi - before_ndvi
            result["ndvi_change"] = round(ndvi_change, 4)

        # ── NDWI change ───────────────────────────────────────────────────────
        before_ndwi = before.get("ndwi_mean")
        after_ndwi = after.get("ndwi_mean")
        if before_ndwi is not None and after_ndwi is not None:
            result["ndwi_change"] = round(after_ndwi - before_ndwi, 4)

        # ── Pixel-level change map ────────────────────────────────────────────
        if before_arr is not None and after_arr is not None:
            # Align shapes (crop to min shape)
            min_h = min(before_arr.shape[0], after_arr.shape[0])
            min_w = min(before_arr.shape[1], after_arr.shape[1])
            b = before_arr[:min_h, :min_w]
            a = after_arr[:min_h, :min_w]

            valid = ~np.isnan(b) & ~np.isnan(a)
            diff = np.where(valid, a - b, np.nan)

            changed = np.abs(diff) > CHANGE_SIGNIFICANCE_THRESHOLD
            total_valid = int(np.sum(valid))
            total_changed = int(np.sum(changed & valid))

            if total_valid > 0:
                change_pct = (total_changed / total_valid) * 100.0
                result["change_percentage"] = round(change_pct, 2)

                # Estimate area (rough: assume total area ~100 km² for now; real data would use CRS)
                result["changed_area_km2"] = round(change_pct, 2)  # placeholder proportional

                # Confidence: higher when we have pixel-level data and large valid coverage
                coverage_ratio = total_valid / (min_h * min_w)
                result["confidence"] = round(min(0.92, 0.55 + coverage_ratio * 0.35), 3)

                # Categorise hotspots (top 5 worst-change regions by 5x5 block averages)
                block = 64  # pixels per block
                hotspots = []
                for r in range(0, min_h - block, block):
                    for c in range(0, min_w - block, block):
                        patch = diff[r:r+block, c:c+block]
                        valid_p = ~np.isnan(patch)
                        if np.sum(valid_p) < block * block * 0.3:
                            continue
                        mean_change = float(np.nanmean(patch))
                        if abs(mean_change) > CHANGE_SIGNIFICANCE_THRESHOLD:
                            hotspots.append({
                                "row": r + block // 2,
                                "col": c + block // 2,
                                "ndvi_change": round(mean_change, 4),
                                "severity": "high" if abs(mean_change) > 0.3 else "medium" if abs(mean_change) > 0.15 else "low",
                            })

                # Take top 10 hotspots sorted by magnitude
                hotspots.sort(key=lambda h: abs(h["ndvi_change"]), reverse=True)
                result["hotspots"] = hotspots[:10]

        # ── Change categories ─────────────────────────────────────────────────
        categories = []
        ndvi_ch = result.get("ndvi_change")
        ndwi_ch = result.get("ndwi_change")

        if ndvi_ch is not None:
            if ndvi_ch < -0.1:
                categories.append({"type": "vegetation_decrease", "magnitude": abs(ndvi_ch), "label": "Estimated Vegetation Decrease"})
                result["change_type"] = "vegetation_decrease"
            elif ndvi_ch > 0.1:
                categories.append({"type": "vegetation_increase", "magnitude": ndvi_ch, "label": "Estimated Vegetation Increase"})
                result["change_type"] = "vegetation_increase"
            else:
                categories.append({"type": "stable_vegetation", "magnitude": abs(ndvi_ch), "label": "Vegetation Largely Stable"})
                result["change_type"] = "stable"

        if ndwi_ch is not None:
            if abs(ndwi_ch) > 0.05:
                label = "Estimated Water Body Change" if abs(ndwi_ch) > 0.2 else "Minor Water-Related Change"
                categories.append({"type": "water_change", "magnitude": abs(ndwi_ch), "label": label})

        result["change_categories"] = categories

        # ── Summary text ──────────────────────────────────────────────────────
        summary_parts = ["Prototype analytical change detection result."]
        if ndvi_ch is not None:
            direction = "decreased" if ndvi_ch < 0 else "increased"
            summary_parts.append(
                f"Estimated NDVI {direction} by {abs(ndvi_ch):.3f} "
                f"(from {before_ndvi:.3f} to {after_ndvi:.3f})."
            )
        if ndwi_ch is not None:
            direction = "decreased" if ndwi_ch < 0 else "increased"
            summary_parts.append(f"Estimated NDWI {direction} by {abs(ndwi_ch):.3f}.")
        if result.get("change_percentage") is not None:
            summary_parts.append(
                f"Approximately {result['change_percentage']:.1f}% of the analysed area "
                f"shows significant spectral change (threshold: |ΔNDVI| > {CHANGE_SIGNIFICANCE_THRESHOLD})."
            )
        summary_parts.append("Analytical confidence: "
                             f"{round(result['confidence']*100)}%. "
                             "These are estimated indicators, not validated measurements.")

        result["summary"] = " ".join(summary_parts)
        return result


change_service = ChangeService()

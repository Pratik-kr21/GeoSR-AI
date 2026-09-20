import httpx
import math
from typing import Optional, Dict, Any, List

# ─── Configurable Weights (must sum to 1.0) ────────────────────────────────────
DEFAULT_WEIGHTS = {
    "vegetation": 0.20,
    "water":      0.15,
    "change":     0.20,
    "weather":    0.15,
    "anomaly":    0.10,
    "flood_terrain_risk": 0.10,
    "slope_instability_risk": 0.10,
}

RISK_LABELS = [
    (0,  25,  "Low"),
    (25, 50,  "Moderate"),
    (50, 75,  "High"),
    (75, 101, "Critical"),
]

METHODOLOGY_VERSION = "v1.0"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def _get_risk_label(score: float) -> str:
    for lo, hi, label in RISK_LABELS:
        if lo <= score < hi:
            return label
    return "Unknown"


class RiskService:
    """
    Computes a prototype GeoRisk Index from available analytical indicators.

    IMPORTANT: This is a prototype analytical tool, not a scientifically or
    commercially validated risk assessment system. Weights and thresholds are
    configurable and explicitly stored with every assessment for full transparency.

    Component sources:
    - vegetation: derived from NDVI (spectral analysis)
    - water: derived from NDWI (spectral analysis)
    - change: derived from change detection results
    - weather: fetched from Open-Meteo (free, no API key)
    - anomaly: derived from statistical anomaly detection count/severity
    """

    async def fetch_weather_score(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Fetch weather anomaly indicators from Open-Meteo.
        Returns a component score (0-100) and raw data.

        Uses: temperature_2m_max, precipitation_sum, windspeed_10m_max
        Score reflects deviation from seasonal norms using available forecast data.
        """
        try:
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,precipitation_sum,windspeed_10m_max",
                "forecast_days": 7,
                "timezone": "auto",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(OPEN_METEO_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

            daily = data.get("daily", {})
            temps = [t for t in (daily.get("temperature_2m_max") or []) if t is not None]
            precip = [p for p in (daily.get("precipitation_sum") or []) if p is not None]
            wind = [w for w in (daily.get("windspeed_10m_max") or []) if w is not None]

            score = 0.0
            factors = []

            # High temperatures increase stress
            if temps:
                avg_temp = sum(temps) / len(temps)
                if avg_temp > 40:
                    score += 30; factors.append(f"Extreme heat (avg {avg_temp:.1f}°C)")
                elif avg_temp > 35:
                    score += 15; factors.append(f"High heat (avg {avg_temp:.1f}°C)")

            # Low precipitation increases drought risk
            if precip:
                total_rain = sum(precip)
                if total_rain < 5:
                    score += 25; factors.append(f"Very low precipitation ({total_rain:.1f}mm/7d)")
                elif total_rain < 20:
                    score += 10; factors.append(f"Low precipitation ({total_rain:.1f}mm/7d)")

            # High winds indicate storm risk
            if wind:
                max_wind = max(wind)
                if max_wind > 60:
                    score += 20; factors.append(f"Strong winds (max {max_wind:.1f}km/h)")
                elif max_wind > 40:
                    score += 8; factors.append(f"Elevated winds (max {max_wind:.1f}km/h)")

            score = min(100.0, score)

            return {
                "score": round(score, 1),
                "available": True,
                "factors": factors,
                "raw": {
                    "avg_temp_max": round(sum(temps)/len(temps), 1) if temps else None,
                    "total_precip_7d": round(sum(precip), 1) if precip else None,
                    "max_windspeed": round(max(wind), 1) if wind else None,
                },
            }
        except Exception as e:
            return {
                "score": 0.0,
                "available": False,
                "reason": str(e),
                "factors": [],
            }

    def compute_vegetation_score(self, ndvi_mean: Optional[float], ndvi_change: Optional[float]) -> Dict[str, Any]:
        """Score 0-100 where 100 = maximum vegetation stress."""
        if ndvi_mean is None:
            return {"score": 0.0, "explanation": "Vegetation indicator unavailable (NDVI not computed)."}

        # Low NDVI → high vegetation stress
        base_stress = max(0.0, (0.5 - ndvi_mean) / 0.7 * 100.0)  # 0.5 is neutral point
        score = min(100.0, max(0.0, base_stress))

        # Add penalty for negative trend
        trend_penalty = 0.0
        trend_text = ""
        if ndvi_change is not None and ndvi_change < -0.05:
            trend_penalty = min(25.0, abs(ndvi_change) * 100.0)
            score = min(100.0, score + trend_penalty)
            trend_text = f" NDVI decreased by {abs(ndvi_change):.3f}, adding {trend_penalty:.0f} points."

        explanation = (
            f"Vegetation stress score {round(score)}. "
            f"Current estimated NDVI: {ndvi_mean:.3f} ({self._ndvi_health_label(ndvi_mean)}).{trend_text}"
        )
        return {"score": round(score, 1), "explanation": explanation}

    def compute_water_score(self, ndwi_mean: Optional[float]) -> Dict[str, Any]:
        """Score 0-100 where 100 = maximum water stress."""
        if ndwi_mean is None:
            return {"score": 0.0, "explanation": "Water indicator unavailable (NDWI not computed)."}

        # Very negative NDWI → severe drought / water stress
        score = max(0.0, min(100.0, (-ndwi_mean + 0.3) / 0.8 * 100.0))
        label = "low water stress" if ndwi_mean > 0 else "moderate water stress" if ndwi_mean > -0.2 else "high water stress"
        explanation = (
            f"Water stress score {round(score)}. "
            f"Estimated NDWI: {ndwi_mean:.3f} ({label})."
        )
        return {"score": round(score, 1), "explanation": explanation}

    def compute_change_score(self, change_pct: Optional[float], ndvi_change: Optional[float]) -> Dict[str, Any]:
        """Score 0-100 based on magnitude of temporal change."""
        if change_pct is None and ndvi_change is None:
            return {"score": 0.0, "explanation": "Temporal change data unavailable."}

        score = 0.0
        parts = []

        if change_pct is not None:
            score += min(60.0, change_pct * 2.0)
            parts.append(f"~{change_pct:.1f}% area with significant spectral change")

        if ndvi_change is not None and ndvi_change < 0:
            trend_score = min(40.0, abs(ndvi_change) * 150.0)
            score = min(100.0, score + trend_score)
            parts.append(f"NDVI trend: {ndvi_change:.3f}")

        explanation = f"Temporal change score {round(score)}. " + (", ".join(parts) if parts else "No change data.") + "."
        return {"score": round(score, 1), "explanation": explanation}

    def compute_anomaly_score(self, anomaly_list: List[Dict]) -> Dict[str, Any]:
        """Score 0-100 based on count and severity of detected anomalies."""
        if not anomaly_list:
            return {"score": 0.0, "explanation": "No anomalies detected in current analysis."}

        severity_weights = {"critical": 25, "high": 15, "medium": 8, "low": 3}
        raw = sum(severity_weights.get(a.get("severity", "low"), 3) for a in anomaly_list)
        score = min(100.0, float(raw))

        counts = {}
        for a in anomaly_list:
            s = a.get("severity", "low")
            counts[s] = counts.get(s, 0) + 1

        count_str = ", ".join(f"{v} {k}" for k, v in counts.items())
        explanation = (
            f"Anomaly score {round(score)} based on {len(anomaly_list)} detected anomaly zone(s): {count_str}."
        )
        return {"score": round(score, 1), "explanation": explanation}

    def compute_flood_terrain_score(self, low_lying_fraction: Optional[float], mean_slope: Optional[float]) -> Dict[str, Any]:
        """Score 0-100 where 100 = high flood terrain risk (very low lying, very flat)."""
        if low_lying_fraction is None or mean_slope is None:
            return {"score": None, "explanation": "Terrain data unavailable."}
            
        # Higher low_lying_fraction -> higher risk
        ll_score = min(100.0, low_lying_fraction * 150.0) 
        
        # Lower mean_slope -> higher flood accumulation risk
        slope_score = max(0.0, 100.0 - (mean_slope * 5.0))
        
        score = (ll_score * 0.7) + (slope_score * 0.3)
        explanation = f"Flood terrain risk score {round(score)} based on {low_lying_fraction*100:.1f}% low-lying area and {mean_slope:.1f}° mean slope."
        return {"score": round(score, 1), "explanation": explanation}

    def compute_slope_instability_score(self, steep_area_fraction: Optional[float], max_slope: Optional[float]) -> Dict[str, Any]:
        """Score 0-100 where 100 = high slope instability risk (steep terrain)."""
        if steep_area_fraction is None or max_slope is None:
            return {"score": None, "explanation": "Terrain data unavailable."}
            
        score = min(100.0, steep_area_fraction * 200.0)
        explanation = f"Slope instability score {round(score)} based on {steep_area_fraction*100:.1f}% steep area (max slope {max_slope:.1f}°)."
        return {"score": round(score, 1), "explanation": explanation}

    def compute_risk(
        self,
        ndvi_mean: Optional[float] = None,
        ndwi_mean: Optional[float] = None,
        ndvi_change: Optional[float] = None,
        change_pct: Optional[float] = None,
        anomaly_list: Optional[List[Dict]] = None,
        weather_data: Optional[Dict] = None,
        terrain_stats: Optional[Dict] = None,
        weights: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Compute the final GeoRisk prototype indicator.

        Args:
            weights: override DEFAULT_WEIGHTS (must sum to ~1.0)
        """
        if weights is None:
            weights = DEFAULT_WEIGHTS.copy()

        # Compute component scores
        veg = self.compute_vegetation_score(ndvi_mean, ndvi_change)
        water = self.compute_water_score(ndwi_mean)
        change = self.compute_change_score(change_pct, ndvi_change)
        anomaly = self.compute_anomaly_score(anomaly_list or [])
        weather_score = weather_data.get("score", 0.0) if weather_data else 0.0
        
        low_lying_frac = terrain_stats.get("low_lying_fraction") if terrain_stats else None
        mean_slope = terrain_stats.get("mean_slope") if terrain_stats else None
        steep_frac = terrain_stats.get("steep_area_fraction") if terrain_stats else None
        max_slope = terrain_stats.get("max_slope") if terrain_stats else None
        
        flood_terrain = self.compute_flood_terrain_score(low_lying_frac, mean_slope)
        slope_inst = self.compute_slope_instability_score(steep_frac, max_slope)

        component_scores = {
            "vegetation": veg["score"],
            "water":      water["score"],
            "change":     change["score"],
            "weather":    weather_score,
            "anomaly":    anomaly["score"],
        }
        
        explanations = {
            "vegetation": veg["explanation"],
            "water": water["explanation"],
            "change": change["explanation"],
            "anomaly": anomaly["explanation"],
            "weather": (
                f"Weather score {round(weather_score)}. " +
                (", ".join(weather_data.get("factors", [])) if weather_data else "Weather data unavailable.")
            ),
        }
        
        # Add terrain components if available, else renormalize weights
        if flood_terrain["score"] is not None:
            component_scores["flood_terrain_risk"] = flood_terrain["score"]
            explanations["flood_terrain_risk"] = flood_terrain["explanation"]
        else:
            weights.pop("flood_terrain_risk", None)
            
        if slope_inst["score"] is not None:
            component_scores["slope_instability_risk"] = slope_inst["score"]
            explanations["slope_instability_risk"] = slope_inst["explanation"]
        else:
            weights.pop("slope_instability_risk", None)
            
        # Renormalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        # Weighted contributions
        weighted_scores = {
            k: round(component_scores.get(k, 0) * weights.get(k, 0), 2)
            for k in weights.keys()
        }

        final_score = min(100.0, sum(weighted_scores.values()))

        # Confidence: lower when key data is missing
        data_available = sum([
            ndvi_mean is not None,
            ndwi_mean is not None,
            ndvi_change is not None,
            bool(anomaly_list),
            weather_data.get("available", False) if weather_data else False,
            terrain_stats is not None,
        ])
        confidence = round(0.40 + (data_available / 6.0) * 0.55, 3)

        # Overall narrative
        dominant = max(weighted_scores, key=lambda k: weighted_scores[k])
        dominant_pct = round(weighted_scores[dominant] / max(final_score, 0.01) * 100, 1)

        narrative = (
            f"Prototype GeoRisk Index: {round(final_score)} ({_get_risk_label(final_score)}). "
            f"The largest contributor is '{dominant}' ({dominant_pct}% of total score). "
            f"{explanations[dominant]} "
            f"Analytical confidence: {round(confidence*100)}%. "
            f"This is a prototype indicator only — not a validated risk assessment."
        )

        return {
            "score": round(final_score, 1),
            "label": _get_risk_label(final_score),
            "confidence": confidence,
            "component_scores": component_scores,
            "weighted_scores": weighted_scores,
            "weights": weights,
            "explanations": explanations,
            "narrative": narrative,
            "methodology_version": METHODOLOGY_VERSION,
            "weather_data": weather_data,
        }

    @staticmethod
    def _ndvi_health_label(ndvi: float) -> str:
        if ndvi < 0.2: return "Very Low Vegetation"
        if ndvi < 0.4: return "Low Vegetation"
        if ndvi < 0.6: return "Moderate Vegetation"
        if ndvi < 0.8: return "Healthy Vegetation"
        return "Very Healthy Vegetation"


risk_service = RiskService()

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class SpectralIndexResponse(BaseModel):
    id: int
    observation_id: int
    project_id: int
    ndvi_mean: Optional[float] = None
    ndvi_min: Optional[float] = None
    ndvi_max: Optional[float] = None
    ndvi_std: Optional[float] = None
    ndvi_p10: Optional[float] = None
    ndvi_p25: Optional[float] = None
    ndvi_p75: Optional[float] = None
    ndvi_p90: Optional[float] = None
    ndvi_health_class: Optional[str] = None
    ndvi_available: Optional[str] = "yes"
    ndwi_mean: Optional[float] = None
    ndwi_min: Optional[float] = None
    ndwi_max: Optional[float] = None
    ndwi_std: Optional[float] = None
    ndwi_water_class: Optional[str] = None
    ndwi_available: Optional[str] = "yes"
    extra_stats: Optional[Dict[str, Any]] = None
    band_mapping_used: Optional[Dict[str, Any]] = None
    band_mapping_warning: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ObservationResponse(BaseModel):
    id: int
    project_id: int
    object_name: str
    satellite: Optional[str] = "Sentinel-2"
    cloud_percentage: Optional[float] = None
    observation_date: Optional[datetime] = None
    bands_count: Optional[int] = None
    band_descriptions: Optional[List[str]] = None
    bbox: Optional[List[float]] = None
    crs: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnomalyResponse(BaseModel):
    id: int
    project_id: int
    observation_id: Optional[int] = None
    anomaly_type: str
    severity: str
    confidence: Optional[float] = None
    center_lat: Optional[float] = None
    center_lon: Optional[float] = None
    area_km2: Optional[float] = None
    evidence: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChangeDetectionRequest(BaseModel):
    before_object_name: str
    after_object_name: str


class ChangeDetectionResponse(BaseModel):
    id: Optional[int] = None
    project_id: int
    before_object_name: Optional[str] = None
    after_object_name: Optional[str] = None
    ndvi_change: Optional[float] = None
    ndwi_change: Optional[float] = None
    change_percentage: Optional[float] = None
    changed_area_km2: Optional[float] = None
    change_type: Optional[str] = None
    change_categories: Optional[List[Dict[str, Any]]] = None
    confidence: Optional[float] = None
    hotspots: Optional[List[Dict[str, Any]]] = None
    summary: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RiskComponentScores(BaseModel):
    vegetation: Optional[float] = None
    water: Optional[float] = None
    change: Optional[float] = None
    weather: Optional[float] = None
    anomaly: Optional[float] = None


class RiskAssessmentResponse(BaseModel):
    id: Optional[int] = None
    project_id: int
    score: float
    label: str
    confidence: Optional[float] = None
    component_scores: Optional[Dict[str, float]] = None
    weighted_scores: Optional[Dict[str, float]] = None
    weights: Optional[Dict[str, float]] = None
    explanations: Optional[Dict[str, str]] = None
    narrative: Optional[str] = None
    weather_data: Optional[Dict[str, Any]] = None
    methodology_version: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class IntelligenceSummaryResponse(BaseModel):
    project_id: int
    observation_id: Optional[int] = None
    ndvi_mean: Optional[float] = None
    ndvi_health_class: Optional[str] = None
    ndwi_mean: Optional[float] = None
    ndwi_water_class: Optional[str] = None
    risk_score: Optional[float] = None
    risk_label: Optional[str] = None
    anomaly_count: int = 0
    change_percentage: Optional[float] = None
    ndvi_change: Optional[float] = None
    band_mapping_warning: Optional[str] = None
    last_analyzed_at: Optional[datetime] = None

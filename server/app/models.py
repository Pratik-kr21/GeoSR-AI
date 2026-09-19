from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from app.database import Base

# ─── Existing models (unchanged) ───────────────────────────────────────────────

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    location = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String, primary_key=True, index=True) # UUID from Celery usually
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending", nullable=False)
    input_resolution = Column(Float, nullable=False)
    target_resolution = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ─── New Intelligence Models ────────────────────────────────────────────────────

class Observation(Base):
    """Represents a single satellite observation (uploaded GeoTIFF) for a project."""
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    object_name = Column(String, nullable=False)         # MinIO object path
    satellite = Column(String, default="Sentinel-2")
    cloud_percentage = Column(Float, nullable=True)
    observation_date = Column(DateTime(timezone=True), nullable=True)
    bands_count = Column(Integer, nullable=True)
    band_descriptions = Column(JSON, nullable=True)      # e.g. ["B02","B03","B04","B08"]
    bbox = Column(JSON, nullable=True)                   # [west, south, east, north] WGS84
    crs = Column(String, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SpectralIndex(Base):
    """NDVI and NDWI statistics computed from an Observation."""
    __tablename__ = "spectral_indices"

    id = Column(Integer, primary_key=True, index=True)
    observation_id = Column(Integer, ForeignKey("observations.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    # NDVI fields
    ndvi_mean = Column(Float, nullable=True)
    ndvi_min = Column(Float, nullable=True)
    ndvi_max = Column(Float, nullable=True)
    ndvi_std = Column(Float, nullable=True)
    ndvi_p10 = Column(Float, nullable=True)
    ndvi_p25 = Column(Float, nullable=True)
    ndvi_p75 = Column(Float, nullable=True)
    ndvi_p90 = Column(Float, nullable=True)
    ndvi_health_class = Column(String, nullable=True)   # e.g. "Moderate Vegetation"
    ndvi_available = Column(String, default="yes")       # "yes" / "no: <reason>"

    # NDWI fields
    ndwi_mean = Column(Float, nullable=True)
    ndwi_min = Column(Float, nullable=True)
    ndwi_max = Column(Float, nullable=True)
    ndwi_std = Column(Float, nullable=True)
    ndwi_water_class = Column(String, nullable=True)    # e.g. "Low Water Presence"
    ndwi_available = Column(String, default="yes")       # "yes" / "no: <reason>"

    # Extra stats JSON (percentiles, histograms, etc.)
    extra_stats = Column(JSON, nullable=True)

    # Band mapping that was detected/used
    band_mapping_used = Column(JSON, nullable=True)      # {"red": 3, "nir": 4, "green": 2}
    band_mapping_warning = Column(Text, nullable=True)   # warning if auto-detected with uncertainty

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ChangeDetection(Base):
    """Temporal change between two observations."""
    __tablename__ = "change_detections"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    before_observation_id = Column(Integer, ForeignKey("observations.id", ondelete="SET NULL"), nullable=True)
    after_observation_id = Column(Integer, ForeignKey("observations.id", ondelete="SET NULL"), nullable=True)

    # Before/after object names (stored even if observation records are missing)
    before_object_name = Column(String, nullable=True)
    after_object_name = Column(String, nullable=True)

    # Aggregate statistics
    ndvi_change = Column(Float, nullable=True)           # after - before mean NDVI
    ndwi_change = Column(Float, nullable=True)
    change_percentage = Column(Float, nullable=True)     # % of area with significant change
    changed_area_km2 = Column(Float, nullable=True)

    # Change characterisation
    change_type = Column(String, nullable=True)          # e.g. "vegetation_decrease"
    change_categories = Column(JSON, nullable=True)      # list of category dicts
    confidence = Column(Float, nullable=True)            # 0.0-1.0
    hotspots = Column(JSON, nullable=True)               # list of {lat, lon, severity}

    # Human-readable summary
    summary = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Anomaly(Base):
    """A single detected spatial anomaly within an observation."""
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    observation_id = Column(Integer, ForeignKey("observations.id", ondelete="CASCADE"), nullable=True)

    anomaly_type = Column(String, nullable=False)        # e.g. "vegetation_stress"
    severity = Column(String, nullable=False)            # "low" / "medium" / "high" / "critical"
    confidence = Column(Float, nullable=True)
    center_lat = Column(Float, nullable=True)
    center_lon = Column(Float, nullable=True)
    area_km2 = Column(Float, nullable=True)
    evidence = Column(JSON, nullable=True)               # {"ndvi_change": -0.21, "z_score": 3.1}
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RiskAssessment(Base):
    """GeoRisk prototype analytical indicator for a project."""
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    # Final score
    score = Column(Float, nullable=False)                # 0-100
    label = Column(String, nullable=False)               # "Low" / "Moderate" / "High" / "Critical"
    confidence = Column(Float, nullable=True)

    # Component scores (raw 0-100 before weighting)
    component_scores = Column(JSON, nullable=False)      # {"vegetation": 70, "water": 40, ...}
    # Weighted component contributions
    weighted_scores = Column(JSON, nullable=False)       # {"vegetation": 21, "water": 8, ...}
    # Weights used
    weights = Column(JSON, nullable=False)               # {"vegetation": 0.30, ...}

    # Explanations per component
    explanations = Column(JSON, nullable=True)           # {"vegetation": "NDVI decreased by 0.18..."}

    # Weather data snapshot
    weather_data = Column(JSON, nullable=True)           # raw Open-Meteo response or null

    methodology_version = Column(String, default="v1.0")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
import os

from app.database import get_db
from app.models import Project, Observation, SpectralIndex as SpectralIndexModel, Anomaly as AnomalyModel, RiskAssessment as RiskAssessmentModel, ChangeDetection as ChangeDetectionModel
from app.services.spectral_service import spectral_service
from app.services.anomaly_service import anomaly_service
from app.services.risk_service import risk_service
from app.services.storage_service import storage_service
from app.services.raster_service import raster_service
from app.schemas.intelligence import (
    SpectralIndexResponse, IntelligenceSummaryResponse
)

router = APIRouter()


async def _get_or_create_observation(
    project_id: int, object_name: str, db: AsyncSession
) -> "Observation":
    """Get existing observation for this object_name or create a new one."""
    result = await db.execute(
        select(Observation).where(
            Observation.project_id == project_id,
            Observation.object_name == object_name,
        )
    )
    obs = result.scalars().first()
    if obs:
        return obs

    # Create a new observation record from raster metadata
    local_path = f"/tmp/obs_meta_{object_name.replace('/', '_')}"
    try:
        storage_service.download_file(object_name, local_path)
        meta = raster_service.read_metadata(local_path)
        bbox_data = raster_service.get_reprojected_bounds(local_path)
        band_info = raster_service.detect_sentinel2_bands(local_path)

        bbox = None
        if "bounds" in bbox_data:
            b = bbox_data["bounds"]  # [[south, west], [north, east]]
            bbox = [b[0][1], b[0][0], b[1][1], b[1][0]]  # [west, south, east, north]

        obs = Observation(
            project_id=project_id,
            object_name=object_name,
            satellite="Sentinel-2",
            bands_count=meta.get("count"),
            band_descriptions=list(band_info.keys()),
            bbox=bbox,
            crs=meta.get("crs"),
            width=meta.get("width"),
            height=meta.get("height"),
        )
    except Exception as e:
        obs = Observation(project_id=project_id, object_name=object_name)
    finally:
        if os.path.exists(local_path):
            os.remove(local_path)

    db.add(obs)
    await db.flush()
    return obs


@router.post("/{project_id}/analyze")
async def analyze_intelligence(
    project_id: int,
    object_name: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger spectral analysis + anomaly detection + risk assessment for a GeoTIFF.
    Uses original Sentinel-2 data, not SRCNN output.
    """
    # Verify project
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get or create observation
    obs = await _get_or_create_observation(project_id, object_name, db)

    # Compute spectral indices
    try:
        si_data = spectral_service.compute_spectral_indices(object_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spectral analysis failed: {str(e)}")

    ndvi_arr = si_data.pop("ndvi_array", None)
    ndwi_arr = si_data.pop("ndwi_array", None)

    # Extra histogram stats
    extra = spectral_service.get_extra_stats(ndvi_arr, ndwi_arr)

    # Save SpectralIndex
    si_record = SpectralIndexModel(
        observation_id=obs.id,
        project_id=project_id,
        ndvi_mean=si_data.get("ndvi_mean"),
        ndvi_min=si_data.get("ndvi_min"),
        ndvi_max=si_data.get("ndvi_max"),
        ndvi_std=si_data.get("ndvi_std"),
        ndvi_p10=si_data.get("ndvi_p10"),
        ndvi_p25=si_data.get("ndvi_p25"),
        ndvi_p75=si_data.get("ndvi_p75"),
        ndvi_p90=si_data.get("ndvi_p90"),
        ndvi_health_class=si_data.get("ndvi_health_class"),
        ndvi_available=si_data.get("ndvi_available", "yes"),
        ndwi_mean=si_data.get("ndwi_mean"),
        ndwi_min=si_data.get("ndwi_min"),
        ndwi_max=si_data.get("ndwi_max"),
        ndwi_std=si_data.get("ndwi_std"),
        ndwi_water_class=si_data.get("ndwi_water_class"),
        ndwi_available=si_data.get("ndwi_available", "yes"),
        extra_stats=extra if extra else None,
        band_mapping_used=si_data.get("band_mapping_used"),
        band_mapping_warning=si_data.get("band_mapping_warning"),
    )
    db.add(si_record)

    # Detect anomalies
    bbox = obs.bbox  # [west, south, east, north]
    detected = anomaly_service.detect_anomalies(ndvi_arr, ndwi_arr, geo_bounds=bbox)

    # Clear old anomalies for this observation
    old_anomalies = await db.execute(
        select(AnomalyModel).where(AnomalyModel.observation_id == obs.id)
    )
    for old in old_anomalies.scalars().all():
        await db.delete(old)

    anomaly_records = []
    for a in detected:
        rec = AnomalyModel(
            project_id=project_id,
            observation_id=obs.id,
            anomaly_type=a["anomaly_type"],
            severity=a["severity"],
            confidence=a.get("confidence"),
            center_lat=a.get("center_lat"),
            center_lon=a.get("center_lon"),
            area_km2=a.get("area_km2"),
            evidence=a.get("evidence"),
            description=a.get("description"),
        )
        db.add(rec)
        anomaly_records.append(rec)

    # Compute risk — fetch weather if we have a centre coordinate
    center_lat, center_lon = None, None
    if bbox and len(bbox) == 4:
        center_lat = (bbox[1] + bbox[3]) / 2
        center_lon = (bbox[0] + bbox[2]) / 2

    weather_data = None
    if center_lat is not None:
        weather_data = await risk_service.fetch_weather_score(center_lat, center_lon)

    # Get latest change stats for this project
    cd_result = await db.execute(
        select(ChangeDetectionModel)
        .where(ChangeDetectionModel.project_id == project_id)
        .order_by(desc(ChangeDetectionModel.created_at))
    )
    latest_cd = cd_result.scalars().first()

    risk_result = risk_service.compute_risk(
        ndvi_mean=si_data.get("ndvi_mean"),
        ndwi_mean=si_data.get("ndwi_mean"),
        ndvi_change=latest_cd.ndvi_change if latest_cd else None,
        change_pct=latest_cd.change_percentage if latest_cd else None,
        anomaly_list=detected,
        weather_data=weather_data,
    )

    # Save risk assessment
    risk_record = RiskAssessmentModel(
        project_id=project_id,
        score=risk_result["score"],
        label=risk_result["label"],
        confidence=risk_result["confidence"],
        component_scores=risk_result["component_scores"],
        weighted_scores=risk_result["weighted_scores"],
        weights=risk_result["weights"],
        explanations=risk_result["explanations"],
        weather_data=weather_data,
        methodology_version=risk_result["methodology_version"],
    )
    db.add(risk_record)

    await db.commit()

    return {
        "message": "Intelligence analysis complete.",
        "observation_id": obs.id,
        "spectral_index_id": si_record.id if si_record.id else None,
        "anomalies_detected": len(detected),
        "risk_score": risk_result["score"],
        "risk_label": risk_result["label"],
        "band_mapping_warning": si_data.get("band_mapping_warning"),
        "ndvi_available": si_data.get("ndvi_available"),
        "ndwi_available": si_data.get("ndwi_available"),
    }


@router.get("/{project_id}/summary", response_model=IntelligenceSummaryResponse)
async def get_intelligence_summary(project_id: int, db: AsyncSession = Depends(get_db)):
    """Return the latest intelligence summary for a project."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Latest spectral index
    si_result = await db.execute(
        select(SpectralIndexModel)
        .where(SpectralIndexModel.project_id == project_id)
        .order_by(desc(SpectralIndexModel.created_at))
    )
    si = si_result.scalars().first()

    # Latest risk
    risk_result = await db.execute(
        select(RiskAssessmentModel)
        .where(RiskAssessmentModel.project_id == project_id)
        .order_by(desc(RiskAssessmentModel.created_at))
    )
    risk = risk_result.scalars().first()

    # Anomaly count
    anomaly_result = await db.execute(
        select(AnomalyModel).where(AnomalyModel.project_id == project_id)
    )
    anomaly_count = len(anomaly_result.scalars().all())

    # Latest change
    cd_result = await db.execute(
        select(ChangeDetectionModel)
        .where(ChangeDetectionModel.project_id == project_id)
        .order_by(desc(ChangeDetectionModel.created_at))
    )
    cd = cd_result.scalars().first()

    return IntelligenceSummaryResponse(
        project_id=project_id,
        observation_id=si.observation_id if si else None,
        ndvi_mean=si.ndvi_mean if si else None,
        ndvi_health_class=si.ndvi_health_class if si else None,
        ndwi_mean=si.ndwi_mean if si else None,
        ndwi_water_class=si.ndwi_water_class if si else None,
        risk_score=risk.score if risk else None,
        risk_label=risk.label if risk else None,
        anomaly_count=anomaly_count,
        change_percentage=cd.change_percentage if cd else None,
        ndvi_change=cd.ndvi_change if cd else None,
        band_mapping_warning=si.band_mapping_warning if si else None,
        last_analyzed_at=si.created_at if si else None,
    )


@router.get("/{project_id}/indices")
async def get_spectral_indices(project_id: int, db: AsyncSession = Depends(get_db)):
    """Return detailed spectral index history for a project."""
    result = await db.execute(
        select(SpectralIndexModel)
        .where(SpectralIndexModel.project_id == project_id)
        .order_by(desc(SpectralIndexModel.created_at))
    )
    records = result.scalars().all()
    return [SpectralIndexResponse.model_validate(r) for r in records]

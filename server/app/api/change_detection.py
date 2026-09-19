from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.database import get_db
from app.models import Project, ChangeDetection as ChangeDetectionModel
from app.services.change_service import change_service
from app.schemas.intelligence import ChangeDetectionRequest, ChangeDetectionResponse

router = APIRouter()


@router.post("/{project_id}", response_model=ChangeDetectionResponse)
async def run_change_detection(
    project_id: int,
    request: ChangeDetectionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Run temporal change detection between two GeoTIFF observations.
    Uses original Sentinel-2 data, not SRCNN output.
    """
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        cd_data = change_service.compare_observations(
            before_object_name=request.before_object_name,
            after_object_name=request.after_object_name,
            project_location=project.location,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Change detection failed: {str(e)}")

    record = ChangeDetectionModel(
        project_id=project_id,
        before_object_name=request.before_object_name,
        after_object_name=request.after_object_name,
        ndvi_change=cd_data.get("ndvi_change"),
        ndwi_change=cd_data.get("ndwi_change"),
        change_percentage=cd_data.get("change_percentage"),
        changed_area_km2=cd_data.get("changed_area_km2"),
        change_type=cd_data.get("change_type"),
        change_categories=cd_data.get("change_categories"),
        confidence=cd_data.get("confidence"),
        hotspots=cd_data.get("hotspots"),
        summary=cd_data.get("summary"),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return ChangeDetectionResponse(
        id=record.id,
        project_id=project_id,
        before_object_name=record.before_object_name,
        after_object_name=record.after_object_name,
        ndvi_change=record.ndvi_change,
        ndwi_change=record.ndwi_change,
        change_percentage=record.change_percentage,
        changed_area_km2=record.changed_area_km2,
        change_type=record.change_type,
        change_categories=record.change_categories,
        confidence=record.confidence,
        hotspots=record.hotspots,
        summary=record.summary,
        created_at=record.created_at,
    )


@router.get("/{project_id}", response_model=ChangeDetectionResponse)
async def get_latest_change_detection(project_id: int, db: AsyncSession = Depends(get_db)):
    """Get the most recent change detection result for a project."""
    result = await db.execute(
        select(ChangeDetectionModel)
        .where(ChangeDetectionModel.project_id == project_id)
        .order_by(desc(ChangeDetectionModel.created_at))
    )
    record = result.scalars().first()
    if not record:
        raise HTTPException(status_code=404, detail="No change detection results found for this project")

    return ChangeDetectionResponse(
        id=record.id,
        project_id=project_id,
        before_object_name=record.before_object_name,
        after_object_name=record.after_object_name,
        ndvi_change=record.ndvi_change,
        ndwi_change=record.ndwi_change,
        change_percentage=record.change_percentage,
        changed_area_km2=record.changed_area_km2,
        change_type=record.change_type,
        change_categories=record.change_categories,
        confidence=record.confidence,
        hotspots=record.hotspots,
        summary=record.summary,
        created_at=record.created_at,
    )

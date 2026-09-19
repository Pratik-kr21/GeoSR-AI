from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.database import get_db
from app.models import Anomaly as AnomalyModel
from app.schemas.intelligence import AnomalyResponse

router = APIRouter()


@router.get("/{project_id}", response_model=List[AnomalyResponse])
async def get_anomalies(project_id: int, db: AsyncSession = Depends(get_db)):
    """Return all detected anomalies for a project, ordered by severity."""
    result = await db.execute(
        select(AnomalyModel).where(AnomalyModel.project_id == project_id)
    )
    anomalies = result.scalars().all()

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    anomalies = sorted(anomalies, key=lambda a: severity_order.get(a.severity, 99))

    return [AnomalyResponse.model_validate(a) for a in anomalies]

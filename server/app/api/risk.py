from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.database import get_db
from app.models import RiskAssessment as RiskAssessmentModel
from app.schemas.intelligence import RiskAssessmentResponse

router = APIRouter()


@router.get("/{project_id}", response_model=RiskAssessmentResponse)
async def get_risk_assessment(project_id: int, db: AsyncSession = Depends(get_db)):
    """Return the latest GeoRisk prototype indicator for a project."""
    result = await db.execute(
        select(RiskAssessmentModel)
        .where(RiskAssessmentModel.project_id == project_id)
        .order_by(desc(RiskAssessmentModel.created_at))
    )
    risk = result.scalars().first()

    if not risk:
        raise HTTPException(
            status_code=404,
            detail="No risk assessment found. Run /intelligence/{project_id}/analyze first."
        )

    return RiskAssessmentResponse(
        id=risk.id,
        project_id=project_id,
        score=risk.score,
        label=risk.label,
        confidence=risk.confidence,
        component_scores=risk.component_scores,
        weighted_scores=risk.weighted_scores,
        weights=risk.weights,
        explanations=risk.explanations,
        weather_data=risk.weather_data,
        methodology_version=risk.methodology_version,
        created_at=risk.created_at,
    )

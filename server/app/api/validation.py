from fastapi import APIRouter
from app.schemas.metrics import ValidationMetrics

router = APIRouter()

@router.get("/{project_id}/metrics", response_model=ValidationMetrics)
async def get_metrics(project_id: int):
    # Mocking validation metrics
    return ValidationMetrics(
        psnr=31.5,
        ssim=0.89,
        lpips=0.12,
        sam=4.2,
        edge_accuracy=0.85,
        geo_consistency=0.92,
        avg_confidence=0.88
    )

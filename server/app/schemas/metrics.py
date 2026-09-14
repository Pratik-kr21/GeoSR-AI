from pydantic import BaseModel
from typing import Optional

class ValidationMetrics(BaseModel):
    psnr: Optional[float] = None
    ssim: Optional[float] = None
    lpips: Optional[float] = None
    sam: Optional[float] = None
    edge_accuracy: Optional[float] = None
    geo_consistency: Optional[float] = None
    avg_confidence: Optional[float] = None
    
    class Config:
        from_attributes = True

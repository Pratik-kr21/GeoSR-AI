from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AnalysisJobBase(BaseModel):
    project_id: int
    status: str = "pending" # pending, processing, completed, failed
    input_resolution: float
    target_resolution: float

class AnalysisJobCreate(AnalysisJobBase):
    pass

class AnalysisJobResponse(AnalysisJobBase):
    id: str # UUID from Celery
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

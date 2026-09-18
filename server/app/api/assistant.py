from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ollama import AsyncClient

from app.schemas.assistant import AssistantQuery, AssistantResponse
from app.database import get_db
from app.models import Project, AnalysisJob
from app.config import settings

router = APIRouter()

@router.post("/{project_id}/assistant", response_model=AssistantResponse)
async def ask_assistant(project_id: int, query: AssistantQuery, db: AsyncSession = Depends(get_db)):
    # Fetch project context to inject into prompt
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Fetch jobs to provide context on the analysis
    jobs_res = await db.execute(select(AnalysisJob).where(AnalysisJob.project_id == project_id))
    jobs = jobs_res.scalars().all()
    job_context = "\n".join([f"- Job {j.id}: Status={j.status}" for j in jobs])

    system_prompt = f"""You are GeoAssist, an AI expert in satellite imagery and super-resolution.
You are helping the user analyze their project '{project.name}' located at '{project.location}'.
The user has the following analysis jobs running or completed:
{job_context if jobs else "No jobs run yet."}

Keep your responses concise, professional, and focus on interpreting geospatial remote sensing data, uncertainty, and resolution metrics (like PSNR/SSIM)."""

    try:
        client = AsyncClient(host=settings.OLLAMA_URL)
        response = await client.chat(
            model=settings.OLLAMA_MODEL,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': query.message}
            ]
        )
        reply = response['message']['content']
        return AssistantResponse(
            response=reply,
            sources=["project_database"]
        )
    except Exception as e:
        print("Ollama Error:", e)
        raise HTTPException(status_code=500, detail="Failed to reach local AI service")

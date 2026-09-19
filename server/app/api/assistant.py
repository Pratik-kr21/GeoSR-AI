from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from ollama import AsyncClient

from app.schemas.assistant import AssistantQuery, AssistantResponse
from app.database import get_db
from app.models import (
    Project, AnalysisJob,
    SpectralIndex as SpectralIndexModel,
    RiskAssessment as RiskAssessmentModel,
    Anomaly as AnomalyModel,
    ChangeDetection as ChangeDetectionModel,
)
from app.config import settings

router = APIRouter()


# ─── Tool Functions ────────────────────────────────────────────────────────────

async def _tool_get_ndvi(project_id: int, db: AsyncSession) -> dict:
    r = await db.execute(
        select(SpectralIndexModel)
        .where(SpectralIndexModel.project_id == project_id)
        .order_by(desc(SpectralIndexModel.created_at))
    )
    si = r.scalars().first()
    if not si:
        return {"available": False, "reason": "No spectral analysis has been run yet."}
    return {
        "available": True,
        "ndvi_mean": si.ndvi_mean,
        "ndvi_min": si.ndvi_min,
        "ndvi_max": si.ndvi_max,
        "ndvi_health_class": si.ndvi_health_class,
        "ndvi_available": si.ndvi_available,
        "ndwi_mean": si.ndwi_mean,
        "ndwi_water_class": si.ndwi_water_class,
        "band_mapping_warning": si.band_mapping_warning,
        "analyzed_at": str(si.created_at),
    }


async def _tool_get_risk(project_id: int, db: AsyncSession) -> dict:
    r = await db.execute(
        select(RiskAssessmentModel)
        .where(RiskAssessmentModel.project_id == project_id)
        .order_by(desc(RiskAssessmentModel.created_at))
    )
    risk = r.scalars().first()
    if not risk:
        return {"available": False, "reason": "No risk assessment found. Run analyze first."}
    return {
        "available": True,
        "score": risk.score,
        "label": risk.label,
        "confidence": risk.confidence,
        "component_scores": risk.component_scores,
        "weighted_scores": risk.weighted_scores,
        "weights": risk.weights,
        "explanations": risk.explanations,
        "methodology_version": risk.methodology_version,
        "assessed_at": str(risk.created_at),
    }


async def _tool_get_anomalies(project_id: int, db: AsyncSession) -> dict:
    r = await db.execute(
        select(AnomalyModel).where(AnomalyModel.project_id == project_id)
    )
    anomalies = r.scalars().all()
    if not anomalies:
        return {"available": True, "count": 0, "anomalies": []}
    return {
        "available": True,
        "count": len(anomalies),
        "anomalies": [
            {
                "type": a.anomaly_type,
                "severity": a.severity,
                "confidence": a.confidence,
                "area_km2": a.area_km2,
                "description": a.description,
            }
            for a in anomalies
        ],
    }


async def _tool_get_change(project_id: int, db: AsyncSession) -> dict:
    r = await db.execute(
        select(ChangeDetectionModel)
        .where(ChangeDetectionModel.project_id == project_id)
        .order_by(desc(ChangeDetectionModel.created_at))
    )
    cd = r.scalars().first()
    if not cd:
        return {"available": False, "reason": "No change detection has been run for this project."}
    return {
        "available": True,
        "ndvi_change": cd.ndvi_change,
        "ndwi_change": cd.ndwi_change,
        "change_percentage": cd.change_percentage,
        "change_type": cd.change_type,
        "confidence": cd.confidence,
        "summary": cd.summary,
        "detected_at": str(cd.created_at),
    }


# ─── Intent detection ──────────────────────────────────────────────────────────

INTENT_KEYWORDS = {
    "ndvi":     ["ndvi", "vegetation", "plant", "green", "forest", "crop", "health"],
    "risk":     ["risk", "score", "index", "hazard", "georisk", "danger", "threat"],
    "anomaly":  ["anomal", "unusual", "stress", "detect", "zone", "hotspot"],
    "change":   ["change", "differ", "before", "after", "temporal", "compare", "decrease", "increase", "trend"],
}


def _detect_intents(message: str) -> list:
    msg_lower = message.lower()
    intents = []
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            intents.append(intent)
    if not intents:
        intents = ["ndvi", "risk"]  # always pull basic context as fallback
    return intents


# ─── Endpoint ──────────────────────────────────────────────────────────────────

@router.post("/{project_id}/assistant", response_model=AssistantResponse)
async def ask_assistant(project_id: int, query: AssistantQuery, db: AsyncSession = Depends(get_db)):
    # Fetch project
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalars().first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Fetch jobs
    jobs_res = await db.execute(select(AnalysisJob).where(AnalysisJob.project_id == project_id))
    jobs = jobs_res.scalars().all()
    job_context = "\n".join([f"- Job {j.id}: Status={j.status}" for j in jobs])

    # ── Tool calls based on intent ──────────────────────────────────────────
    intents = _detect_intents(query.message)
    tool_data = {}
    sources_used = []

    if "ndvi" in intents:
        tool_data["spectral_indices"] = await _tool_get_ndvi(project_id, db)
        sources_used.append("spectral_analysis_tool")

    if "risk" in intents:
        tool_data["risk_assessment"] = await _tool_get_risk(project_id, db)
        sources_used.append("risk_assessment_tool")

    if "anomaly" in intents:
        tool_data["anomalies"] = await _tool_get_anomalies(project_id, db)
        sources_used.append("anomaly_detection_tool")

    if "change" in intents:
        tool_data["change_detection"] = await _tool_get_change(project_id, db)
        sources_used.append("change_detection_tool")

    # Always add basic project context
    sources_used.append("project_database")

    # Format tool data for LLM context
    import json
    tool_context = json.dumps(tool_data, indent=2, default=str)

    system_prompt = f"""You are GeoAssist, an AI Decision Intelligence agent for satellite geospatial analysis.
You are helping the user analyze project '{project.name}' located at '{project.location}'.

IMPORTANT RULES:
1. Do NOT fabricate or estimate any numerical values. Only use data from the ANALYTICAL DATA section below.
2. If data is unavailable (available=false), say so clearly rather than guessing.
3. Always mention confidence levels when discussing analytical indicators.
4. Clearly distinguish analytical estimates from validated ground truth.
5. Use terminology: "Estimated", "Prototype Indicator", "Analytical Confidence: X%", "Detected Anomaly".

ANALYSIS JOBS:
{job_context if jobs else "No super-resolution jobs run yet."}

ANALYTICAL DATA (fetched from real backend tools — do NOT modify these values):
{tool_context}

Based on the above real data, answer the user's question. Be concise and evidence-based.
If no analysis has been run, suggest the user run the intelligence analysis first.
"""

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
            sources=sources_used
        )
    except Exception as e:
        print("Ollama Error:", e)
        # Graceful degradation: return the tool data as plain text if Ollama is down
        fallback = f"GeoAssist AI is temporarily unavailable. Here is the raw analytical data:\n\n{tool_context}"
        return AssistantResponse(
            response=fallback,
            sources=sources_used
        )


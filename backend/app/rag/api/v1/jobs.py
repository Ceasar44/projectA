from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.rag.services import job_service

router = APIRouter(prefix="/jobs", tags=["rag-jobs"])


@router.get("")
async def list_jobs(
    kb_name: str = Query(..., description="Knowledge base name"),
    limit: int = Query(200, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
):
    return {"success": True, "data": await job_service.list_jobs(session, kb_name, limit=limit)}


@router.get("/{job_id}")
async def get_job(job_id: str, session: AsyncSession = Depends(get_session)):
    return {"success": True, "data": await job_service.get_job_detail(session, job_id)}


@router.post("/{job_id}/upsert")
async def upsert_job(job_id: str, session: AsyncSession = Depends(get_session)):
    result = await job_service.upsert_job_to_milvus(session, job_id)
    await session.commit()
    return {"success": True, "message": "Vectorization complete", "data": result}

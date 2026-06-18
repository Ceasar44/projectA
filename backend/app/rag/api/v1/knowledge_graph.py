import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.rag.db import get_kb_repository
from app.rag.services import file_service, kg_graph_sync_service

router = APIRouter(prefix="/knowledge-graph", tags=["rag-knowledge-graph"])
logger = logging.getLogger(__name__)


@router.get("/kb/{kb_name}")
async def get_kb_graph(kb_name: str, session: AsyncSession = Depends(get_session)):
    kb = await get_kb_repository(session).get_by_name(kb_name)
    if not kb:
        raise HTTPException(status_code=404, detail=f"Knowledge base not found: {kb_name}")

    files_result = await file_service.list_files(session, kb_name, limit=1000)
    synced_files = [item for item in files_result.get("files", []) if item.get("sync_graph") and item.get("job")]

    all_triples = []
    file_graphs = []
    for item in synced_files:
        job = item.get("job") or {}
        job_id = job.get("id") if isinstance(job, dict) else None
        if not job_id:
            continue
        try:
            result = await kg_graph_sync_service.get_kg_graph_sync_service().query_graph(
                job_id=job_id,
                kb_name=kb_name,
            )
            triples = result.get("triples", [])
            all_triples.extend(triples)
            file_graphs.append(
                {
                    "file_id": item["id"],
                    "file_name": item["file_name"],
                    "job_id": job_id,
                    "triples_count": len(triples),
                    "triples": triples,
                }
            )
        except Exception as exc:
            logger.warning("Knowledge graph query failed", extra={"file_id": item["id"], "error": str(exc)})
            file_graphs.append(
                {
                    "file_id": item["id"],
                    "file_name": item["file_name"],
                    "job_id": job_id,
                    "triples_count": 0,
                    "triples": [],
                    "error": str(exc),
                }
            )

    return {
        "success": True,
        "data": {
            "kb_name": kb_name,
            "files": file_graphs,
            "total_files": len(file_graphs),
            "total_triples": len(all_triples),
        },
    }

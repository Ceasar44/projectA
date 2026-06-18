import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.core.exceptions import NotFoundError
from app.rag.db import (
    get_category_file_repository,
    get_category_repository,
    get_chunk_image_repository,
    get_file_repository,
    get_job_repository,
    get_kb_repository,
)
from app.rag.services.oss_service import get_oss_service

logger = logging.getLogger(__name__)


async def list_files(session: AsyncSession, kb_name: str, limit: int = 200) -> dict:
    kb = await get_kb_repository(session).get_by_name(kb_name)
    if not kb:
        return {"files": [], "total": 0}

    files = await get_file_repository(session).list_by_kb(kb["id"], limit=limit)
    job_repo = get_job_repository(session)
    result = []
    for file_record in files:
        job = await job_repo.get_by_file(file_record["id"])
        result.append({**file_record, "job": job})
    return {"files": result, "total": len(result)}


async def delete_file(session: AsyncSession, file_id: str) -> str:
    file_repo = get_file_repository(session)
    file_record = await file_repo.get_by_id(file_id)
    if not file_record:
        raise NotFoundError("File record not found")

    file_name = file_record["file_name"]
    kb = await get_kb_repository(session).get_by_id(file_record["kb_id"])
    kb_name = kb["name"] if kb else None
    job = await get_job_repository(session).get_by_file(file_id)

    if job and kb_name:
        job_id = job["id"]
        try:
            from app.rag.services.milvus_service import get_milvus_service

            get_milvus_service().delete_by_job(kb_name, job_id)
        except Exception as exc:
            logger.warning("Failed to delete Milvus vectors", extra={"job_id": job_id, "error": str(exc)})

        if file_record.get("sync_graph"):
            try:
                from app.rag.services.kg_graph_sync_service import get_kg_graph_sync_service

                await get_kg_graph_sync_service().delete_graph_by_job(job_id)
            except Exception as exc:
                logger.warning("Failed to delete knowledge graph data", extra={"job_id": job_id, "error": str(exc)})

        try:
            oss_keys = await get_chunk_image_repository(session).get_oss_keys_by_job(job_id)
            if oss_keys:
                get_oss_service().delete_objects(oss_keys)
        except Exception as exc:
            logger.warning("Failed to delete chunk images from OSS", extra={"error": str(exc)})

    category_file_id = file_record.get("category_file_id")
    if category_file_id:
        try:
            category_file_repo = get_category_file_repository(session)
            category_file = await category_file_repo.get_by_id(category_file_id)
            if category_file:
                category = await get_category_repository(session).get(category_file["category_id"])
                if category and category["name"] == "__default__":
                    await category_file_repo.delete(category_file_id)
        except Exception as exc:
            logger.warning("Failed to clean default category file", extra={"error": str(exc)})

    await file_repo.delete(file_id)
    return file_name


async def batch_delete_files(session: AsyncSession, file_ids: list[str], kb_name: str) -> dict:
    deleted: list[str] = []
    failed: list[dict[str, str]] = []
    for file_id in file_ids:
        try:
            deleted.append(await delete_file(session, file_id))
        except Exception as exc:
            logger.error("Failed to delete file", extra={"file_id": file_id, "error": str(exc)})
            failed.append({"file_id": file_id, "error": str(exc)})
    return {"deleted": deleted, "failed": failed}

import asyncio
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.core.exceptions import ExternalServiceError, ForbiddenError, NotFoundError
from app.rag.db import (
    get_chunk_image_repository,
    get_chunk_repository,
    get_file_repository,
    get_job_repository,
    get_kb_repository,
)
from app.rag.services.chunk_cleaner import clean_single_chunk_with_llm
from app.rag.services.oss_service import get_oss_service

logger = logging.getLogger(__name__)


async def delete_job_images_from_oss(session: AsyncSession, job_id: str) -> None:
    try:
        oss_keys = await get_chunk_image_repository(session).get_oss_keys_by_job(job_id)
        if oss_keys:
            get_oss_service().delete_objects(oss_keys)
    except Exception as exc:
        logger.warning("Failed to delete job images from OSS", extra={"job_id": job_id, "error": str(exc)})


async def check_not_vectorized(session: AsyncSession, job_id: str) -> None:
    job = await get_job_repository(session).get(job_id)
    if job and job.get("vectorized"):
        raise ForbiddenError("This job has already been vectorized and cannot be edited")


async def get_chunks_by_job(session: AsyncSession, job_id: str) -> dict:
    chunks = await get_chunk_repository(session).get_by_job(job_id)
    return {"job_id": job_id, "chunks": chunks, "total": len(chunks)}


async def list_all_job_ids(session: AsyncSession) -> list[str]:
    return await get_chunk_repository(session).list_all_job_ids()


async def edit_chunk(session: AsyncSession, job_id: str, chunk_index: int, content: str) -> None:
    await check_not_vectorized(session, job_id)
    chunk_repo = get_chunk_repository(session)
    if not await chunk_repo.get_by_job_and_index(job_id, chunk_index):
        raise NotFoundError(f"Chunk not found: job_id={job_id}, chunk_index={chunk_index}")
    await chunk_repo.update_content_by_index(job_id, chunk_index, content, status="edited")


async def clean_single_chunk(
    session: AsyncSession,
    job_id: str,
    chunk_index: int,
    instruction: str | None = None,
) -> str:
    await check_not_vectorized(session, job_id)
    chunk_repo = get_chunk_repository(session)
    chunk = await chunk_repo.get_by_job_and_index(job_id, chunk_index)
    if not chunk:
        raise NotFoundError(f"Chunk not found: job_id={job_id}, chunk_index={chunk_index}")
    cleaned = await asyncio.to_thread(
        clean_single_chunk_with_llm,
        chunk.get("current_content") or "",
        instruction,
    )
    await chunk_repo.update_content_by_index(job_id, chunk_index, cleaned, status="cleaned")
    return cleaned


async def revert_single_chunk(session: AsyncSession, job_id: str, chunk_index: int) -> None:
    await check_not_vectorized(session, job_id)
    chunk_repo = get_chunk_repository(session)
    if not await chunk_repo.get_by_job_and_index(job_id, chunk_index):
        raise NotFoundError(f"Chunk not found: job_id={job_id}, chunk_index={chunk_index}")
    await chunk_repo.revert_chunk_by_index(job_id, chunk_index)


async def clean_job_chunks(session: AsyncSession, job_id: str, instruction: str | None = None) -> dict:
    await check_not_vectorized(session, job_id)
    chunk_repo = get_chunk_repository(session)
    chunks = await chunk_repo.get_by_job(job_id)
    if not chunks:
        raise NotFoundError("This job has no chunks")

    errors = []
    for chunk in chunks:
        try:
            cleaned = await asyncio.to_thread(
                clean_single_chunk_with_llm,
                chunk["current_content"],
                instruction,
            )
            await chunk_repo.update_content(chunk["chunk_id"], cleaned, "cleaned")
        except Exception as exc:
            errors.append({"chunk_id": chunk["chunk_id"], "error": str(exc)})
    return {"success": len(chunks) - len(errors), "failed": len(errors), "total": len(chunks), "errors": errors}


async def revert_job_chunks(session: AsyncSession, job_id: str) -> None:
    await check_not_vectorized(session, job_id)
    await get_chunk_repository(session).revert_job(job_id)


async def clean_all_chunks(session: AsyncSession, instruction: str | None = None) -> dict:
    chunk_repo = get_chunk_repository(session)
    job_ids = await chunk_repo.list_all_job_ids()
    success = 0
    failed = 0
    for job_id in job_ids:
        for chunk in await chunk_repo.get_by_job(job_id):
            try:
                cleaned = await asyncio.to_thread(
                    clean_single_chunk_with_llm,
                    chunk["current_content"],
                    instruction,
                )
                await chunk_repo.update_content(chunk["chunk_id"], cleaned, "cleaned")
                success += 1
            except Exception:
                failed += 1
    return {"success": success, "failed": failed}


async def revert_all_chunks(session: AsyncSession) -> None:
    await get_chunk_repository(session).revert_all()


async def upsert_job_chunks(session: AsyncSession, job_id: str) -> dict:
    from app.rag.services.job_service import upsert_job_to_milvus

    return await upsert_job_to_milvus(session, job_id)


async def batch_upsert_jobs(session: AsyncSession, job_ids: list[str]) -> dict:
    succeeded = []
    failed = []
    job_repo = get_job_repository(session)
    for job_id in job_ids:
        try:
            job = await job_repo.get(job_id)
            if job and job.get("vectorized"):
                continue
            await upsert_job_chunks(session, job_id)
            succeeded.append(job_id)
        except ForbiddenError:
            pass
        except Exception as exc:
            logger.error("Batch upsert failed", extra={"job_id": job_id, "error": str(exc)})
            failed.append({"job_id": job_id, "error": str(exc)})
    return {"succeeded": succeeded, "failed": failed}


async def get_chunk_images(session: AsyncSession, job_id: str, chunk_index: int) -> list[dict]:
    chunk = await get_chunk_repository(session).get_by_job_and_index(job_id, chunk_index)
    if not chunk:
        return []
    records = await get_chunk_image_repository(session).get_by_chunk(chunk["chunk_id"])
    oss_service = get_oss_service()
    for record in records:
        if record.get("oss_key"):
            try:
                record["oss_url"] = oss_service.get_presigned_url(record["oss_key"], expires=3600)
            except Exception as exc:
                logger.warning("Failed to create image presigned URL", extra={"error": str(exc)})
                record["oss_url"] = ""
    return records


async def add_chunk_image(
    session: AsyncSession,
    job_id: str,
    chunk_index: int,
    file_content: bytes,
    filename: str,
    insert_position: int = 0,
    page: int | None = None,
) -> dict:
    await check_not_vectorized(session, job_id)
    chunk_repo = get_chunk_repository(session)
    chunk = await chunk_repo.get_by_job_and_index(job_id, chunk_index)
    if not chunk:
        raise NotFoundError(f"Chunk not found: job_id={job_id}, chunk_index={chunk_index}")

    job = await get_job_repository(session).get(job_id)
    if not job:
        raise NotFoundError("Job not found")
    kb = await get_kb_repository(session).get_by_id(job["kb_id"])
    kb_name = kb["name"] if kb else "unknown"
    file_record = await get_file_repository(session).get_by_id(job["file_id"])
    file_name = file_record["file_name"] if file_record else "unknown"

    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
    placeholder_hex = uuid.uuid4().hex[:8]
    placeholder = f"<<IMAGE:{placeholder_hex}>>"
    try:
        oss_key = get_oss_service().upload_file(
            f"conversation_assets/{kb_name}/{file_name}/{placeholder_hex}",
            f"image.{ext}",
            file_content,
        )
    except Exception as exc:
        raise ExternalServiceError(f"OSS upload failed: {exc}") from exc

    image_repo = get_chunk_image_repository(session)
    sort_order = len(await image_repo.get_by_chunk(chunk["chunk_id"]))
    record = await image_repo.insert(
        chunk_id=chunk["chunk_id"],
        job_id=job_id,
        placeholder=placeholder,
        oss_key=oss_key,
        page=page,
        sort_order=sort_order,
    )

    try:
        record["oss_url"] = get_oss_service().get_presigned_url(oss_key, expires=3600)
    except Exception:
        record["oss_url"] = ""

    content = chunk.get("current_content") or ""
    position = max(0, min(insert_position, len(content)))
    await chunk_repo.update_content_by_index(
        job_id,
        chunk_index,
        content[:position] + placeholder + content[position:],
        status="edited",
    )
    return record


async def delete_chunk_image(session: AsyncSession, job_id: str, chunk_index: int, image_id: str) -> None:
    await check_not_vectorized(session, job_id)
    image_repo = get_chunk_image_repository(session)
    record = await image_repo.get_by_id(image_id)
    if not record:
        raise NotFoundError("Image record not found")

    if record.get("oss_key"):
        try:
            get_oss_service().delete_objects([record["oss_key"]])
        except Exception as exc:
            logger.warning("Failed to delete image OSS object", extra={"error": str(exc)})
    await image_repo.delete(image_id)

    placeholder = record.get("placeholder", "")
    if placeholder:
        chunk_repo = get_chunk_repository(session)
        chunk = await chunk_repo.get_by_job_and_index(job_id, chunk_index)
        if chunk:
            await chunk_repo.update_content_by_index(
                job_id,
                chunk_index,
                (chunk.get("current_content") or "").replace(placeholder, ""),
                status="edited",
            )


async def resolve_image_placeholders(session: AsyncSession, placeholders: list[str]) -> dict[str, str]:
    if not placeholders:
        return {}
    records = await get_chunk_image_repository(session).get_by_placeholders(placeholders)
    oss_service = get_oss_service()
    result = {}
    for record in records:
        placeholder = record.get("placeholder", "")
        oss_key = record.get("oss_key", "")
        if placeholder and oss_key:
            try:
                result[placeholder] = oss_service.get_presigned_url(oss_key, expires=3600)
            except Exception as exc:
                logger.warning("Failed to resolve image placeholder", extra={"error": str(exc)})
    return result

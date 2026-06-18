import asyncio
import io
import logging
import re
from pathlib import Path

import pandas as pd
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.core.exceptions import ConflictError, ExternalServiceError, NotFoundError, ValidationError
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

ALLOWED_EXT = {".pdf", ".doc", ".docx", ".txt", ".md", ".ppt", ".pptx", ".xlsx", ".xls"}
SAFE_FILENAME_RE = re.compile(r"^[\w\u4e00-\u9fff\-\. ]+$")


def validate_file(filename: str, size: int) -> None:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXT:
        raise ValidationError(f"Unsupported file type: {ext}")
    if size > 200 * 1024 * 1024:
        raise ValidationError("File exceeds 200MB")
    if not SAFE_FILENAME_RE.match(filename):
        raise ValidationError("File name contains unsupported characters")


async def get_kb_or_raise(session: AsyncSession, kb_name: str) -> dict:
    kb = await get_kb_repository(session).get_by_name(kb_name)
    if not kb:
        raise NotFoundError(f"Knowledge base not found: {kb_name}")
    return kb


async def upload_document(
    session: AsyncSession,
    file_name: str,
    file_content: bytes,
    kb_name: str,
    background_tasks: BackgroundTasks,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    image_dpi: int = 150,
    sync_graph: bool = False,
) -> dict:
    validate_file(file_name, len(file_content))
    kb = await get_kb_or_raise(session, kb_name)
    oss_key = f"kb/{kb_name}/{file_name}"

    file_repo = get_file_repository(session)
    existing = await file_repo.get_by_kb_and_oss_key(kb["id"], oss_key)
    if existing:
        raise ConflictError(f"File already exists in knowledge base: {file_name}")

    try:
        get_oss_service().upload_bytes(oss_key, file_content)
    except Exception as exc:
        raise ExternalServiceError(f"OSS upload failed: {exc}") from exc

    from app.rag.services.category_service import get_or_create_default_category

    default_category = await get_or_create_default_category(session)
    category_file_repo = get_category_file_repository(session)
    existing_category_file = await category_file_repo.get_by_category_and_filename(default_category["id"], file_name)
    if existing_category_file:
        await category_file_repo.delete(existing_category_file["id"])
    category_file = await category_file_repo.create(
        category_id=default_category["id"],
        file_name=file_name,
        oss_key=oss_key,
    )

    file_record = await file_repo.create(
        kb_id=kb["id"],
        file_name=file_name,
        oss_key=oss_key,
        category_file_id=category_file["id"],
        file_size=len(file_content),
        mime_type=guess_mime(file_name),
        status="pending",
        sync_graph=sync_graph,
    )
    job = await get_job_repository(session).create(file_id=file_record["id"], kb_id=kb["id"])
    await session.commit()

    background_tasks.add_task(
        run_pipeline,
        job_id=job["id"],
        file_id=file_record["id"],
        kb_id=kb["id"],
        kb_name=kb_name,
        file_name=file_name,
        oss_key=oss_key,
        image_mode=kb["image_mode"],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        image_dpi=image_dpi,
        sync_graph=sync_graph,
    )

    return {"job_id": job["id"], "file_id": file_record["id"], "file_name": file_name, "sync_graph": sync_graph}


async def upload_to_category(
    session: AsyncSession,
    file_name: str,
    file_content: bytes,
    category_id: str,
) -> dict:
    validate_file(file_name, len(file_content))
    category = await get_category_repository(session).get(category_id)
    if not category:
        raise NotFoundError("Category not found")

    oss_key = get_oss_service().upload_file(f"category/{category['name']}", file_name, file_content)
    category_file_repo = get_category_file_repository(session)
    existing = await category_file_repo.get_by_category_and_filename(category_id, file_name)
    if existing:
        await category_file_repo.delete(existing["id"])
    return await category_file_repo.create(category_id=category_id, file_name=file_name, oss_key=oss_key)


async def batch_upload_to_category(session: AsyncSession, files: list[tuple[str, bytes]], category_id: str) -> dict:
    category = await get_category_repository(session).get(category_id)
    if not category:
        raise NotFoundError("Category not found")

    succeeded = []
    failed = []
    for raw_name, content in files:
        file_name = raw_name.replace("\\", "/").split("/")[-1]
        try:
            record = await upload_to_category(session, file_name, content, category_id)
            succeeded.append({"file_name": file_name, "success": True, "record": record})
        except Exception as exc:
            failed.append({"file_name": file_name, "error": str(exc)})
    return {"succeeded": succeeded, "failed": failed, "total": len(files)}


async def start_chunking(
    session: AsyncSession,
    category_id: str,
    kb_name: str,
    background_tasks: BackgroundTasks,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    image_dpi: int = 150,
    sync_graph: bool = False,
    excel_rows_per_chunk: int = 50,
) -> dict:
    category = await get_category_repository(session).get(category_id)
    if not category:
        raise NotFoundError("Category not found")
    kb = await get_kb_or_raise(session, kb_name)
    category_files = await get_category_file_repository(session).list_by_category(category_id)
    return await submit_category_files_for_chunking(
        session=session,
        background_tasks=background_tasks,
        kb=kb,
        kb_name=kb_name,
        category_files=category_files,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        image_dpi=image_dpi,
        sync_graph=sync_graph,
        excel_rows_per_chunk=excel_rows_per_chunk,
    )


async def start_chunking_excel(
    session: AsyncSession,
    category_id: str,
    kb_name: str,
    background_tasks: BackgroundTasks,
    excel_rows_per_chunk: int = 50,
    excel_configs: list | None = None,
) -> dict:
    category = await get_category_repository(session).get(category_id)
    if not category:
        raise NotFoundError("Category not found")
    kb = await get_kb_or_raise(session, kb_name)
    config_map = {
        item["category_file_id"]: item.get("column_config")
        for item in (excel_configs or [])
        if item.get("category_file_id")
    }
    category_files = [
        item
        for item in await get_category_file_repository(session).list_by_category(category_id)
        if item["file_name"].lower().rsplit(".", 1)[-1] in ("xlsx", "xls")
    ]
    return await submit_category_files_for_chunking(
        session=session,
        background_tasks=background_tasks,
        kb=kb,
        kb_name=kb_name,
        category_files=category_files,
        chunk_size=500,
        chunk_overlap=0,
        image_dpi=150,
        sync_graph=False,
        excel_rows_per_chunk=excel_rows_per_chunk,
        excel_config_map=config_map,
    )


async def submit_category_files_for_chunking(
    *,
    session: AsyncSession,
    background_tasks: BackgroundTasks,
    kb: dict,
    kb_name: str,
    category_files: list[dict],
    chunk_size: int,
    chunk_overlap: int,
    image_dpi: int,
    sync_graph: bool,
    excel_rows_per_chunk: int,
    excel_config_map: dict | None = None,
) -> dict:
    if not category_files:
        return {"submitted": 0, "files": [], "skipped": [], "errors": []}

    file_repo = get_file_repository(session)
    job_repo = get_job_repository(session)
    submitted = []
    skipped = []
    errors = []

    for category_file in category_files:
        file_name = category_file["file_name"]
        oss_key = category_file["oss_key"]
        try:
            existing = await file_repo.get_by_kb_and_oss_key(kb["id"], oss_key)
            if existing:
                skipped.append({"file_name": file_name, "reason": "already exists"})
                continue
            file_record = await file_repo.create(
                kb_id=kb["id"],
                file_name=file_name,
                oss_key=oss_key,
                category_file_id=category_file["id"],
                status="pending",
                sync_graph=sync_graph,
            )
            job = await job_repo.create(file_id=file_record["id"], kb_id=kb["id"])
            background_tasks.add_task(
                run_pipeline,
                job_id=job["id"],
                file_id=file_record["id"],
                kb_id=kb["id"],
                kb_name=kb_name,
                file_name=file_name,
                oss_key=oss_key,
                image_mode=kb["image_mode"],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                image_dpi=image_dpi,
                sync_graph=sync_graph,
                excel_rows_per_chunk=excel_rows_per_chunk,
                excel_column_config=(excel_config_map or {}).get(category_file["id"]),
            )
            submitted.append({"file_name": file_name, "job_id": job["id"]})
        except Exception as exc:
            errors.append({"file_name": file_name, "error": str(exc)})

    await session.commit()
    return {"submitted": len(submitted), "files": submitted, "skipped": skipped, "errors": errors}


async def get_excel_columns(session: AsyncSession, category_file_id: str) -> dict:
    category_file = await get_category_file_repository(session).get_by_id(category_file_id)
    if not category_file:
        raise NotFoundError("Category file not found")
    file_name = category_file["file_name"]
    ext = file_name.lower().rsplit(".", 1)[-1]
    if ext not in ("xlsx", "xls"):
        raise ValidationError(f"File is not Excel: {file_name}")
    file_content = get_oss_service().get_object_bytes(category_file["oss_key"])
    sheets = pd.read_excel(
        io.BytesIO(file_content),
        sheet_name=None,
        header=0,
        dtype=str,
        keep_default_na=False,
        nrows=0,
    )
    return {
        "file_name": file_name,
        "category_file_id": category_file_id,
        "sheets": {name: list(frame.columns) for name, frame in sheets.items()},
    }


async def search_documents(
    session: AsyncSession,
    query: str,
    kb_name: str,
    top_k: int = 10,
    filter_expr: str | None = None,
    ranker: str = "RRF",
    hybrid_alpha: float = 0.5,
    keyword_filter: str | None = None,
    rerank: bool = False,
    rerank_model: str = "qwen3-rerank",
    rerank_top_n: int | None = None,
) -> list:
    from app.rag.services.milvus_service import get_milvus_service

    hits = get_milvus_service().hybrid_search(
        collection_name=kb_name,
        query=query,
        top_k=top_k,
        filter_expr=filter_expr,
        ranker=ranker,
        hybrid_alpha=hybrid_alpha,
        keyword_filter=keyword_filter or None,
    )

    if hits:
        try:
            chunk_ids = [item["chunk_id"] for item in hits if item.get("chunk_id")]
            image_records = await get_chunk_image_repository(session).get_by_chunk_ids(chunk_ids)
            oss_service = get_oss_service()
            image_map_by_chunk = {}
            for record in image_records:
                placeholder = record.get("placeholder", "")
                oss_key = record.get("oss_key", "")
                if placeholder and oss_key:
                    try:
                        image_map_by_chunk.setdefault(record["chunk_id"], {})[placeholder] = (
                            oss_service.get_presigned_url(oss_key, expires=3600)
                        )
                    except Exception:
                        pass
            for hit in hits:
                hit["image_map"] = image_map_by_chunk.get(hit.get("chunk_id"), {})
        except Exception as exc:
            logger.warning("Failed to enrich search results with image URLs", extra={"error": str(exc)})
            for hit in hits:
                hit.setdefault("image_map", {})

    if rerank and hits:
        from app.rag.services.rerank_service import get_rerank_service

        hits = get_rerank_service().rerank(
            query=query,
            chunks=hits,
            model=rerank_model,
            top_n=int(rerank_top_n) if rerank_top_n else len(hits),
        )
    return hits


async def run_pipeline(**kwargs) -> None:
    from app.rag.services.job_service import run_job_pipeline

    await run_job_pipeline(**kwargs)


def guess_mime(file_name: str) -> str:
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
    return {
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
        "md": "text/markdown",
        "ppt": "application/vnd.ms-powerpoint",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel",
    }.get(ext, "application/octet-stream")

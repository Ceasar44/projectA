import asyncio
import logging
import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.rag.core.exceptions import NotFoundError
from app.rag.db import (
    get_chunk_image_repository,
    get_chunk_repository,
    get_file_repository,
    get_job_repository,
    get_kb_repository,
)

logger = logging.getLogger(__name__)

_UPSERT_BATCH = 100


async def list_jobs(session: AsyncSession, kb_name: str, limit: int = 200) -> dict:
    kb = await get_kb_repository(session).get_by_name(kb_name)
    if not kb:
        return {"jobs": [], "total": 0}
    jobs = await get_job_repository(session).list_by_kb(kb["id"], limit=limit)
    return {"jobs": jobs, "total": len(jobs)}


async def get_job_detail(session: AsyncSession, job_id: str) -> dict:
    job = await get_job_repository(session).get(job_id)
    if not job:
        raise NotFoundError("Job not found")
    return {"job": job}


async def run_job_pipeline(
    job_id: str,
    file_id: str,
    kb_id: str,
    kb_name: str,
    file_name: str,
    oss_key: str,
    image_mode: bool,
    chunk_size: int,
    chunk_overlap: int,
    image_dpi: int,
    sync_graph: bool = False,
    excel_rows_per_chunk: int = 50,
    excel_column_config: dict | None = None,
) -> None:
    async with SessionLocal() as session:
        try:
            await _run_job_pipeline_with_session(
                session=session,
                job_id=job_id,
                file_id=file_id,
                kb_id=kb_id,
                kb_name=kb_name,
                file_name=file_name,
                oss_key=oss_key,
                image_mode=image_mode,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                image_dpi=image_dpi,
                sync_graph=sync_graph,
                excel_rows_per_chunk=excel_rows_per_chunk,
                excel_column_config=excel_column_config,
            )
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def _run_job_pipeline_with_session(
    *,
    session: AsyncSession,
    job_id: str,
    file_id: str,
    kb_id: str,
    kb_name: str,
    file_name: str,
    oss_key: str,
    image_mode: bool,
    chunk_size: int,
    chunk_overlap: int,
    image_dpi: int,
    sync_graph: bool = False,
    excel_rows_per_chunk: int = 50,
    excel_column_config: dict | None = None,
) -> None:
    job_repo = get_job_repository(session)
    file_repo = get_file_repository(session)

    try:
        await job_repo.update_status(job_id, "chunking", stage="Chunking document")
        await file_repo.update_status(file_id, "processing")
        await session.flush()

        file_content = await asyncio.to_thread(_download_file, oss_key)
        if image_mode:
            chunks, image_records = await asyncio.to_thread(
                _parse_image_mode,
                file_content,
                job_id,
                kb_name,
                file_name,
                chunk_size,
                chunk_overlap,
                image_dpi,
            )
        else:
            chunks = await asyncio.to_thread(
                _parse_text_mode,
                file_content,
                file_name,
                chunk_size,
                chunk_overlap,
                excel_rows_per_chunk,
                excel_column_config,
            )
            image_records = []

        from app.rag.services.chunk_service import delete_job_images_from_oss

        await delete_job_images_from_oss(session, job_id)

        kb = await get_kb_repository(session).get_by_id(kb_id)
        metadata_fields = kb.get("metadata_fields") or [] if kb else []
        inject_map = {
            item["key"]: file_name.rsplit(".", 1)[0]
            for item in metadata_fields
            if item.get("auto_inject") == "filename_prefix" and item.get("key")
        }
        if inject_map:
            for chunk in chunks:
                metadata = chunk.get("metadata") or {}
                metadata.update(inject_map)
                chunk["metadata"] = metadata

        chunk_repo = get_chunk_repository(session)
        if image_mode:
            await chunk_repo.bulk_insert_with_ids(job_id, file_name, chunks)
        else:
            await chunk_repo.bulk_insert(job_id, file_name, chunks)

        if image_records:
            await get_chunk_image_repository(session).bulk_insert(image_records)

        chunk_count = len(chunks)
        await job_repo.update_status(
            job_id,
            "chunked",
            stage="Chunking complete; ready for vectorization",
            chunk_count=chunk_count,
            progress=50,
        )
        await file_repo.update_status(file_id, "chunked")
        logger.info("[RAG pipeline] Chunking complete", extra={"job_id": job_id, "chunk_count": chunk_count})
    except Exception as exc:
        logger.exception("[RAG pipeline] Job failed", extra={"job_id": job_id})
        await job_repo.update_status(job_id, "error", stage="Processing failed", error_msg=str(exc))
        await file_repo.update_status(file_id, "error", error_msg=str(exc))


async def upsert_job_to_milvus(session: AsyncSession, job_id: str) -> dict:
    job_repo = get_job_repository(session)
    job = await job_repo.get(job_id)
    if not job:
        raise NotFoundError("Job not found")

    file_record = await get_file_repository(session).get_by_id(job["file_id"])
    kb = await get_kb_repository(session).get_by_id(job["kb_id"])
    if not file_record or not kb:
        raise NotFoundError("File or knowledge base not found")

    pg_chunks = await get_chunk_repository(session).get_by_job(job_id)
    if not pg_chunks:
        raise NotFoundError("This job has no chunks")

    milvus_chunks = [
        {
            "chunk_id": chunk["chunk_id"],
            "job_id": job_id,
            "file_name": file_record["file_name"],
            "chunk_index": chunk["chunk_index"],
            "content": chunk["current_content"],
            "metadata": chunk.get("metadata") or {},
        }
        for chunk in pg_chunks
        if chunk.get("current_content")
    ]

    from app.rag.services.milvus_service import get_milvus_service

    milvus_service = get_milvus_service()
    milvus_service.get_or_create_collection(
        kb["name"],
        dim=kb["vector_dim"],
        kb_type=kb.get("kb_type", "standard"),
        image_vector_dim=kb.get("retrieval_config", {}).get("image_vector_dim", 1024),
    )

    if kb.get("kb_type") == "multimodal":
        result = await asyncio.to_thread(_upsert_multimodal_chunks, session, kb, job_id, milvus_chunks)
    else:
        result = await asyncio.to_thread(_upsert_chunks_in_batches, milvus_service, kb, milvus_chunks)

    failed_batches = result.get("failed_batches", [])
    if failed_batches:
        await job_repo.update_status(
            job_id,
            "chunked",
            stage=f"Vectorization partially failed: {failed_batches}",
        )
        return result

    await job_repo.mark_vectorized(job_id)

    if file_record.get("sync_graph"):
        try:
            from app.rag.services.kg_graph_sync_service import get_kg_graph_sync_service

            await get_kg_graph_sync_service().sync_chunks_to_graph(
                job_id=job_id,
                kb_name=kb["name"],
                file_name=file_record["file_name"],
                chunks=[
                    {
                        "chunk_id": chunk["chunk_id"],
                        "content": chunk["current_content"],
                        "chunk_index": chunk["chunk_index"],
                        "vector": [],
                    }
                    for chunk in pg_chunks
                    if chunk.get("current_content")
                ],
            )
        except Exception as exc:
            logger.warning("Knowledge graph sync failed", extra={"job_id": job_id, "error": str(exc)})

    return result


def _upsert_chunks_in_batches(milvus_service, kb: dict, chunks: list[dict]) -> dict:
    from app.rag.services.embedding_service import get_embedding_service

    image_placeholder_re = re.compile(r"<<IMAGE:[0-9a-f]+>>")
    kb_name = kb["name"]
    vector_dim = kb["vector_dim"]
    metadata_fields = kb.get("metadata_fields") or []
    fulltext_keys = [item["key"] for item in metadata_fields if item.get("fulltext") and item.get("key")]
    embedding_service = get_embedding_service()

    original_model = embedding_service.model
    if kb.get("embedding_model") and kb["embedding_model"] != original_model:
        embedding_service.model = kb["embedding_model"]

    total_upserted = 0
    failed_batches = []
    total_batches = (len(chunks) + _UPSERT_BATCH - 1) // _UPSERT_BATCH

    try:
        for batch_start in range(0, len(chunks), _UPSERT_BATCH):
            batch = chunks[batch_start : batch_start + _UPSERT_BATCH]
            batch_no = batch_start // _UPSERT_BATCH + 1
            texts = []
            for chunk in batch:
                clean = image_placeholder_re.sub("", chunk["content"]).strip()
                if fulltext_keys:
                    metadata = chunk.get("metadata") or {}
                    prefix = "\n".join(f"{key}: {metadata[key]}" for key in fulltext_keys if metadata.get(key))
                    texts.append(f"{prefix}\n\n{clean}" if prefix else clean)
                else:
                    texts.append(clean)

            try:
                vectors = embedding_service.embed_texts(texts, dimension=vector_dim)
                data = []
                for chunk, vector, indexed_content in zip(batch, vectors, texts):
                    row = {
                        "chunk_id": chunk["chunk_id"],
                        "job_id": chunk.get("job_id", ""),
                        "file_name": chunk.get("file_name", ""),
                        "chunk_index": int(chunk.get("chunk_index", 0)),
                        "content": indexed_content,
                        "dense": vector,
                    }
                    for key, value in (chunk.get("metadata") or {}).items():
                        row.setdefault(key, value)
                    data.append(row)
                response = milvus_service.client.upsert(collection_name=kb_name, data=data)
                total_upserted += response.get("upsert_count", len(data))
            except Exception as exc:
                logger.error("Milvus upsert batch failed", extra={"batch": batch_no, "error": str(exc)})
                failed_batches.append(batch_no)
    finally:
        embedding_service.model = original_model

    return {"upsert_count": total_upserted, "failed_batches": failed_batches, "total_batches": total_batches}


def _upsert_multimodal_chunks(session: AsyncSession, kb: dict, job_id: str, chunks: list[dict]) -> dict:
    from app.rag.services.milvus_service import get_milvus_service
    from app.rag.services.multimodal_embedding_service import get_multimodal_embedding_service

    # Multimodal repository image lookups are async. Keep this function limited
    # to text vectors for now, matching the standard upsert path.
    multimodal_service = get_multimodal_embedding_service()
    milvus_service = get_milvus_service()
    image_placeholder_re = re.compile(r"<<IMAGE:[0-9a-f]+>>")
    image_dim = kb.get("vector_dim", 1024)
    data = []

    for chunk in chunks:
        clean_content = image_placeholder_re.sub("", chunk["content"]).strip()
        if not clean_content:
            continue
        text_vec = multimodal_service.embed_text(clean_content, dimension=image_dim)
        row = {
            "chunk_id": chunk["chunk_id"],
            "job_id": job_id,
            "file_name": chunk.get("file_name", ""),
            "chunk_index": int(chunk.get("chunk_index", 0)),
            "content": clean_content,
            "dense": text_vec,
            "image_dense": [0.0] * image_dim,
        }
        for key, value in (chunk.get("metadata") or {}).items():
            row.setdefault(key, value)
        data.append(row)

    if not data:
        return {"upsert_count": 0}
    response = milvus_service.client.upsert(collection_name=kb["name"], data=data)
    return {"upsert_count": response.get("upsert_count", len(data))}


def _download_file(oss_key: str) -> bytes:
    from app.rag.services.oss_service import get_oss_service

    return get_oss_service().get_object_bytes(oss_key)


def _parse_image_mode(
    file_content: bytes,
    job_id: str,
    kb_name: str,
    file_name: str,
    chunk_size: int,
    chunk_overlap: int,
    image_dpi: int,
):
    from app.rag.services.doc_image_parser import parse_pdf, parse_word

    ext = file_name.lower().rsplit(".", 1)[-1]
    if ext == "pdf":
        return parse_pdf(
            file_content=file_content,
            job_id=job_id,
            collection=kb_name,
            file_name=file_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            image_dpi=image_dpi,
        )
    if ext in ("docx", "doc"):
        return parse_word(
            file_content=file_content,
            job_id=job_id,
            collection=kb_name,
            file_name=file_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
    raise ValueError(f"Image mode does not support .{ext}")


def _parse_text_mode(
    file_content: bytes,
    file_name: str,
    chunk_size: int,
    chunk_overlap: int,
    excel_rows_per_chunk: int = 50,
    excel_column_config: dict | None = None,
) -> list:
    from app.rag.services.chunk_splitter import split_excel, split_text_with_metadata

    ext = file_name.lower().rsplit(".", 1)[-1]
    if ext in ("xlsx", "xls"):
        return split_excel(
            file_content=file_content,
            file_name=file_name,
            rows_per_chunk=excel_rows_per_chunk,
            base_metadata={"file_name": file_name, "source": ext},
            column_config=excel_column_config,
        )

    text = _extract_text(file_content, ext)
    return split_text_with_metadata(
        text=text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        base_metadata={"file_name": file_name, "source": ext},
    )


def _extract_text(file_content: bytes, ext: str) -> str:
    if ext == "pdf":
        import fitz

        doc = fitz.open(stream=file_content, filetype="pdf")
        return "\n\n".join(page.get_text() for page in doc)
    if ext in ("docx", "doc"):
        import io

        from docx import Document

        doc = Document(io.BytesIO(file_content))
        return "\n\n".join(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())
    if ext in ("txt", "md"):
        for encoding in ("utf-8", "gbk", "utf-16"):
            try:
                return file_content.decode(encoding)
            except UnicodeDecodeError:
                continue
    return file_content.decode("utf-8", errors="ignore")

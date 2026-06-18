import uuid
from typing import Any

from sqlalchemy import delete, distinct, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.rag import (
    RagConversationMessage,
    RagConversationSession,
    RagKnowledgeBase,
    RagKnowledgeCategory,
    RagKnowledgeCategoryFile,
    RagKnowledgeChunk,
    RagKnowledgeChunkImage,
    RagKnowledgeChunkOrigin,
    RagKnowledgeFile,
    RagKnowledgeJob,
)


def _dt(value) -> str | None:
    return value.isoformat() if value else None


class BaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def flush_refresh(self, row):
        await self.session.flush()
        await self.session.refresh(row)
        return row


class KbRepository(BaseRepository):
    async def create(
        self,
        *,
        name: str,
        display_name: str | None = None,
        description: str | None = None,
        image_mode: bool = False,
        kb_type: str = "standard",
        embedding_model: str = "text-embedding-v3",
        vector_dim: int = 1536,
        metadata_fields: list | None = None,
        retrieval_config: dict | None = None,
    ) -> dict[str, Any]:
        row = RagKnowledgeBase(
            name=name,
            display_name=display_name or name,
            description=description,
            image_mode=image_mode,
            kb_type=kb_type,
            embedding_model=embedding_model,
            vector_dim=vector_dim,
            metadata_fields=metadata_fields or [],
            retrieval_config=retrieval_config or {},
        )
        self.session.add(row)
        await self.flush_refresh(row)
        return self._normalize(row)

    async def get_by_id(self, kb_id: str) -> dict[str, Any] | None:
        row = await self.session.get(RagKnowledgeBase, kb_id)
        return self._normalize(row) if row else None

    async def get_by_name(self, name: str) -> dict[str, Any] | None:
        row = await self.session.scalar(select(RagKnowledgeBase).where(RagKnowledgeBase.name == name).limit(1))
        return self._normalize(row) if row else None

    async def list_all(self) -> list[dict[str, Any]]:
        rows = (await self.session.scalars(select(RagKnowledgeBase).order_by(RagKnowledgeBase.created_at.desc()))).all()
        return [self._normalize(row) for row in rows]

    async def update(self, kb_id: str, **values) -> dict[str, Any] | None:
        row = await self.session.get(RagKnowledgeBase, kb_id)
        if not row:
            return None
        for key, value in values.items():
            if value is not None:
                setattr(row, key, value)
        await self.flush_refresh(row)
        return self._normalize(row)

    async def delete(self, kb_id: str) -> None:
        await self.session.execute(delete(RagKnowledgeBase).where(RagKnowledgeBase.id == kb_id))

    @staticmethod
    def _normalize(row: RagKnowledgeBase) -> dict[str, Any]:
        return {
            "id": row.id,
            "name": row.name,
            "display_name": row.display_name,
            "description": row.description,
            "image_mode": bool(row.image_mode),
            "kb_type": row.kb_type,
            "embedding_model": row.embedding_model,
            "vector_dim": row.vector_dim,
            "metadata_fields": row.metadata_fields or [],
            "retrieval_config": row.retrieval_config or {},
            "created_at": _dt(row.created_at),
            "updated_at": _dt(row.updated_at),
        }


class CategoryRepository(BaseRepository):
    async def create(self, *, name: str, description: str | None = None) -> dict[str, Any]:
        row = RagKnowledgeCategory(name=name, description=description)
        self.session.add(row)
        await self.flush_refresh(row)
        return self._normalize(row)

    async def get(self, category_id: str) -> dict[str, Any] | None:
        row = await self.session.get(RagKnowledgeCategory, category_id)
        return self._normalize(row) if row else None

    async def get_by_name(self, name: str) -> dict[str, Any] | None:
        row = await self.session.scalar(
            select(RagKnowledgeCategory).where(RagKnowledgeCategory.name == name).limit(1)
        )
        return self._normalize(row) if row else None

    async def list_all(self) -> list[dict[str, Any]]:
        rows = (
            await self.session.scalars(select(RagKnowledgeCategory).order_by(RagKnowledgeCategory.created_at.desc()))
        ).all()
        return [self._normalize(row) for row in rows]

    async def update(self, category_id: str, *, name: str | None = None, description: str | None = None) -> None:
        values = {}
        if name is not None:
            values["name"] = name
        if description is not None:
            values["description"] = description
        if values:
            await self.session.execute(update(RagKnowledgeCategory).where(RagKnowledgeCategory.id == category_id).values(**values))

    async def delete(self, category_id: str) -> None:
        await self.session.execute(delete(RagKnowledgeCategory).where(RagKnowledgeCategory.id == category_id))

    @staticmethod
    def _normalize(row: RagKnowledgeCategory) -> dict[str, Any]:
        return {
            "id": row.id,
            "category_id": row.id,
            "name": row.name,
            "description": row.description,
            "created_at": _dt(row.created_at),
            "updated_at": _dt(row.updated_at),
        }


class CategoryFileRepository(BaseRepository):
    async def create(self, *, category_id: str, file_name: str, oss_key: str) -> dict[str, Any]:
        row = RagKnowledgeCategoryFile(category_id=category_id, file_name=file_name, oss_key=oss_key)
        self.session.add(row)
        await self.flush_refresh(row)
        return self._normalize(row)

    async def get_by_id(self, file_id: str) -> dict[str, Any] | None:
        row = await self.session.get(RagKnowledgeCategoryFile, file_id)
        return self._normalize(row) if row else None

    async def get_by_category_and_filename(self, category_id: str, file_name: str) -> dict[str, Any] | None:
        row = await self.session.scalar(
            select(RagKnowledgeCategoryFile)
            .where(RagKnowledgeCategoryFile.category_id == category_id, RagKnowledgeCategoryFile.file_name == file_name)
            .limit(1)
        )
        return self._normalize(row) if row else None

    async def list_by_category(self, category_id: str) -> list[dict[str, Any]]:
        rows = (
            await self.session.scalars(
                select(RagKnowledgeCategoryFile)
                .where(RagKnowledgeCategoryFile.category_id == category_id)
                .order_by(RagKnowledgeCategoryFile.created_at.desc())
            )
        ).all()
        return [self._normalize(row) for row in rows]

    async def count_by_category(self, category_id: str) -> int:
        return await self.session.scalar(
            select(func.count()).select_from(RagKnowledgeCategoryFile).where(RagKnowledgeCategoryFile.category_id == category_id)
        ) or 0

    async def delete(self, file_id: str) -> None:
        await self.session.execute(delete(RagKnowledgeCategoryFile).where(RagKnowledgeCategoryFile.id == file_id))

    async def delete_by_category_and_filename(self, category_id: str, file_name: str) -> None:
        await self.session.execute(
            delete(RagKnowledgeCategoryFile).where(
                RagKnowledgeCategoryFile.category_id == category_id,
                RagKnowledgeCategoryFile.file_name == file_name,
            )
        )

    @staticmethod
    def _normalize(row: RagKnowledgeCategoryFile) -> dict[str, Any]:
        return {
            "id": row.id,
            "category_id": row.category_id,
            "file_name": row.file_name,
            "oss_key": row.oss_key,
            "created_at": _dt(row.created_at),
        }


class FileRepository(BaseRepository):
    async def create(self, **values) -> dict[str, Any]:
        row = RagKnowledgeFile(**values)
        self.session.add(row)
        await self.flush_refresh(row)
        return self._normalize(row)

    async def get_by_id(self, file_id: str) -> dict[str, Any] | None:
        row = await self.session.get(RagKnowledgeFile, file_id)
        return self._normalize(row) if row else None

    async def get_by_kb_and_oss_key(self, kb_id: str, oss_key: str) -> dict[str, Any] | None:
        row = await self.session.scalar(
            select(RagKnowledgeFile).where(RagKnowledgeFile.kb_id == kb_id, RagKnowledgeFile.oss_key == oss_key).limit(1)
        )
        return self._normalize(row) if row else None

    async def get_by_kb_and_filename(self, kb_id: str, file_name: str) -> dict[str, Any] | None:
        row = await self.session.scalar(
            select(RagKnowledgeFile)
            .where(RagKnowledgeFile.kb_id == kb_id, RagKnowledgeFile.file_name == file_name)
            .order_by(RagKnowledgeFile.created_at.desc())
            .limit(1)
        )
        return self._normalize(row) if row else None

    async def list_by_kb(self, kb_id: str, limit: int = 500) -> list[dict[str, Any]]:
        rows = (
            await self.session.scalars(
                select(RagKnowledgeFile)
                .where(RagKnowledgeFile.kb_id == kb_id)
                .order_by(RagKnowledgeFile.created_at.desc())
                .limit(limit)
            )
        ).all()
        return [self._normalize(row) for row in rows]

    async def update_status(self, file_id: str, status: str, error_msg: str | None = None) -> None:
        await self.session.execute(
            update(RagKnowledgeFile).where(RagKnowledgeFile.id == file_id).values(status=status, error_msg=error_msg)
        )

    async def update_sync_graph(self, file_id: str, sync_graph: bool) -> None:
        await self.session.execute(
            update(RagKnowledgeFile).where(RagKnowledgeFile.id == file_id).values(sync_graph=sync_graph)
        )

    async def delete(self, file_id: str) -> None:
        await self.session.execute(delete(RagKnowledgeFile).where(RagKnowledgeFile.id == file_id))

    async def delete_by_kb(self, kb_id: str) -> None:
        await self.session.execute(delete(RagKnowledgeFile).where(RagKnowledgeFile.kb_id == kb_id))

    @staticmethod
    def _normalize(row: RagKnowledgeFile) -> dict[str, Any]:
        return {
            "id": row.id,
            "kb_id": row.kb_id,
            "category_file_id": row.category_file_id,
            "file_name": row.file_name,
            "oss_key": row.oss_key,
            "file_size": row.file_size,
            "mime_type": row.mime_type,
            "status": row.status,
            "error_msg": row.error_msg,
            "sync_graph": row.sync_graph,
            "created_at": _dt(row.created_at),
            "updated_at": _dt(row.updated_at),
        }


class JobRepository(BaseRepository):
    async def create(self, *, file_id: str, kb_id: str) -> dict[str, Any]:
        row = RagKnowledgeJob(file_id=file_id, kb_id=kb_id)
        self.session.add(row)
        await self.flush_refresh(row)
        return self._normalize(row)

    async def get(self, job_id: str) -> dict[str, Any] | None:
        row = await self.session.get(RagKnowledgeJob, job_id)
        return self._normalize(row) if row else None

    async def get_by_file(self, file_id: str) -> dict[str, Any] | None:
        row = await self.session.scalar(
            select(RagKnowledgeJob).where(RagKnowledgeJob.file_id == file_id).order_by(RagKnowledgeJob.created_at.desc()).limit(1)
        )
        return self._normalize(row) if row else None

    async def list_by_kb(self, kb_id: str, limit: int = 500) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(RagKnowledgeJob, RagKnowledgeFile.file_name, RagKnowledgeFile.oss_key)
                .join(RagKnowledgeFile, RagKnowledgeFile.id == RagKnowledgeJob.file_id)
                .where(RagKnowledgeJob.kb_id == kb_id)
                .order_by(RagKnowledgeJob.created_at.desc())
                .limit(limit)
            )
        ).all()
        return [self._normalize(row[0], file_name=row.file_name, oss_key=row.oss_key) for row in rows]

    async def update_status(self, job_id: str, status: str, **values) -> None:
        update_values = {"status": status, **{key: value for key, value in values.items() if value is not None}}
        await self.session.execute(update(RagKnowledgeJob).where(RagKnowledgeJob.id == job_id).values(**update_values))

    async def mark_vectorized(self, job_id: str) -> None:
        await self.session.execute(
            update(RagKnowledgeJob)
            .where(RagKnowledgeJob.id == job_id)
            .values(vectorized=True, status="done", progress=100)
        )

    async def delete(self, job_id: str) -> None:
        await self.session.execute(delete(RagKnowledgeJob).where(RagKnowledgeJob.id == job_id))

    async def delete_by_file(self, file_id: str) -> None:
        await self.session.execute(delete(RagKnowledgeJob).where(RagKnowledgeJob.file_id == file_id))

    @staticmethod
    def _normalize(row: RagKnowledgeJob, *, file_name: str | None = None, oss_key: str | None = None) -> dict[str, Any]:
        return {
            "id": row.id,
            "job_id": row.id,
            "file_id": row.file_id,
            "kb_id": row.kb_id,
            "status": row.status,
            "stage": row.stage,
            "progress": row.progress,
            "chunk_count": row.chunk_count,
            "vectorized": row.vectorized,
            "error_msg": row.error_msg,
            "file_name": file_name,
            "oss_key": oss_key,
            "created_at": _dt(row.created_at),
            "updated_at": _dt(row.updated_at),
        }


class ChunkRepository(BaseRepository):
    async def bulk_insert(self, job_id: str, file_name: str, chunks: list[dict[str, Any]]) -> None:
        await self._bulk_insert(job_id, chunks, use_existing_ids=False)

    async def bulk_insert_with_ids(self, job_id: str, file_name: str, chunks: list[dict[str, Any]]) -> None:
        await self._bulk_insert(job_id, chunks, use_existing_ids=True)

    async def _bulk_insert(self, job_id: str, chunks: list[dict[str, Any]], *, use_existing_ids: bool) -> None:
        await self.delete_by_job(job_id)
        for idx, chunk in enumerate(chunks):
            chunk_id = str(chunk.get("chunk_id") or uuid.uuid4()) if use_existing_ids else str(uuid.uuid4())
            content = chunk.get("page_content") or chunk.get("content") or ""
            chunk_index = int(chunk.get("chunk_index", idx))
            row = RagKnowledgeChunk(
                id=chunk_id,
                job_id=job_id,
                chunk_index=chunk_index,
                content=content,
                metadata_json=chunk.get("metadata") or {},
            )
            self.session.add(row)
            self.session.add(RagKnowledgeChunkOrigin(chunk_id=chunk_id, content=content))
        await self.session.flush()

    async def get_by_job(self, job_id: str) -> list[dict[str, Any]]:
        rows = (
            await self.session.scalars(
                select(RagKnowledgeChunk).where(RagKnowledgeChunk.job_id == job_id).order_by(RagKnowledgeChunk.chunk_index.asc())
            )
        ).all()
        return [self._normalize(row) for row in rows]

    async def get_by_job_and_index(self, job_id: str, chunk_index: int) -> dict[str, Any] | None:
        row = await self.session.scalar(
            select(RagKnowledgeChunk)
            .where(RagKnowledgeChunk.job_id == job_id, RagKnowledgeChunk.chunk_index == chunk_index)
            .limit(1)
        )
        return self._normalize(row) if row else None

    async def get_by_id(self, chunk_id: str) -> dict[str, Any] | None:
        row = await self.session.get(RagKnowledgeChunk, chunk_id)
        return self._normalize(row) if row else None

    async def get_by_ids(self, chunk_ids: list[str]) -> list[dict[str, Any]]:
        if not chunk_ids:
            return []
        rows = (await self.session.scalars(select(RagKnowledgeChunk).where(RagKnowledgeChunk.id.in_(chunk_ids)))).all()
        return [self._normalize(row) for row in rows]

    async def get_by_ids_with_file_names(self, chunk_ids: list[str]) -> list[dict[str, Any]]:
        if not chunk_ids:
            return []
        rows = (
            await self.session.execute(
                select(RagKnowledgeChunk, RagKnowledgeFile.file_name)
                .join(RagKnowledgeJob, RagKnowledgeJob.id == RagKnowledgeChunk.job_id)
                .join(RagKnowledgeFile, RagKnowledgeFile.id == RagKnowledgeJob.file_id, isouter=True)
                .where(RagKnowledgeChunk.id.in_(chunk_ids))
            )
        ).all()
        result = []
        for row in rows:
            item = self._normalize(row[0])
            item["file_name"] = row.file_name or ""
            item["metadata"] = {**(item.get("metadata") or {}), "file_name": row.file_name or ""}
            result.append(item)
        return result

    async def list_all_job_ids(self) -> list[str]:
        rows = (await self.session.scalars(select(distinct(RagKnowledgeChunk.job_id)))).all()
        return [str(row) for row in rows if row]

    async def has_chunks(self, job_id: str) -> bool:
        count = await self.session.scalar(select(func.count()).select_from(RagKnowledgeChunk).where(RagKnowledgeChunk.job_id == job_id))
        return bool(count)

    async def update_content_by_index(self, job_id: str, chunk_index: int, content: str, status: str = "edited") -> None:
        await self.session.execute(
            update(RagKnowledgeChunk)
            .where(RagKnowledgeChunk.job_id == job_id, RagKnowledgeChunk.chunk_index == chunk_index)
            .values(content=content, is_modified=status != "original")
        )

    async def update_content(self, chunk_id: str, content: str, status: str = "edited") -> None:
        await self.session.execute(
            update(RagKnowledgeChunk).where(RagKnowledgeChunk.id == chunk_id).values(content=content, is_modified=status != "original")
        )

    async def revert_chunk_by_index(self, job_id: str, chunk_index: int) -> None:
        chunk = await self.session.scalar(
            select(RagKnowledgeChunk).where(RagKnowledgeChunk.job_id == job_id, RagKnowledgeChunk.chunk_index == chunk_index)
        )
        if chunk:
            await self.revert_chunk(chunk.id)

    async def revert_chunk(self, chunk_id: str) -> None:
        origin = await self.session.get(RagKnowledgeChunkOrigin, chunk_id)
        if origin:
            await self.update_content(chunk_id, origin.content, status="original")

    async def revert_job(self, job_id: str) -> None:
        rows = (await self.session.scalars(select(RagKnowledgeChunk).where(RagKnowledgeChunk.job_id == job_id))).all()
        for row in rows:
            await self.revert_chunk(row.id)

    async def revert_all(self) -> None:
        rows = (await self.session.scalars(select(RagKnowledgeChunk))).all()
        for row in rows:
            await self.revert_chunk(row.id)

    async def delete_by_job(self, job_id: str) -> None:
        await self.session.execute(delete(RagKnowledgeChunk).where(RagKnowledgeChunk.job_id == job_id))

    async def delete_chunk(self, chunk_id: str) -> None:
        await self.session.execute(delete(RagKnowledgeChunk).where(RagKnowledgeChunk.id == chunk_id))

    @staticmethod
    def _normalize(row: RagKnowledgeChunk) -> dict[str, Any]:
        return {
            "chunk_id": row.id,
            "job_id": row.job_id,
            "chunk_index": row.chunk_index,
            "current_content": row.content,
            "original_content": row.content,
            "content": row.content,
            "is_modified": row.is_modified,
            "status": "edited" if row.is_modified else "original",
            "metadata": row.metadata_json or {},
            "updated_at": _dt(row.updated_at),
        }


class ChunkImageRepository(BaseRepository):
    async def bulk_insert(self, records: list[dict[str, Any]]) -> None:
        for record in records:
            self.session.add(
                RagKnowledgeChunkImage(
                    chunk_id=record["chunk_id"],
                    placeholder=record.get("placeholder", ""),
                    oss_key=record.get("oss_key", ""),
                    page=record.get("page"),
                    sort_order=record.get("sort_order", 0),
                )
            )
        await self.session.flush()

    async def insert(self, **values) -> dict[str, Any]:
        values.pop("job_id", None)
        values.pop("oss_url", None)
        row = RagKnowledgeChunkImage(**values)
        self.session.add(row)
        await self.flush_refresh(row)
        return self._normalize(row)

    async def get_by_id(self, record_id: str) -> dict[str, Any] | None:
        row = await self.session.get(RagKnowledgeChunkImage, record_id)
        return self._normalize(row) if row else None

    async def get_by_chunk(self, chunk_id: str) -> list[dict[str, Any]]:
        rows = (
            await self.session.scalars(
                select(RagKnowledgeChunkImage)
                .where(RagKnowledgeChunkImage.chunk_id == chunk_id)
                .order_by(RagKnowledgeChunkImage.sort_order.asc(), RagKnowledgeChunkImage.created_at.asc())
            )
        ).all()
        return [self._normalize(row) for row in rows]

    async def get_by_chunk_ids(self, chunk_ids: list[str]) -> list[dict[str, Any]]:
        if not chunk_ids:
            return []
        rows = (
            await self.session.scalars(
                select(RagKnowledgeChunkImage)
                .where(RagKnowledgeChunkImage.chunk_id.in_(chunk_ids))
                .order_by(RagKnowledgeChunkImage.chunk_id, RagKnowledgeChunkImage.sort_order.asc())
            )
        ).all()
        return [self._normalize(row) for row in rows]

    async def get_by_placeholders(self, placeholders: list[str]) -> list[dict[str, Any]]:
        if not placeholders:
            return []
        rows = (
            await self.session.scalars(
                select(RagKnowledgeChunkImage).where(RagKnowledgeChunkImage.placeholder.in_(placeholders))
            )
        ).all()
        return [self._normalize(row) for row in rows]

    async def get_oss_keys_by_job(self, job_id: str) -> list[str]:
        rows = (
            await self.session.scalars(
                select(RagKnowledgeChunkImage.oss_key)
                .join(RagKnowledgeChunk, RagKnowledgeChunk.id == RagKnowledgeChunkImage.chunk_id)
                .where(RagKnowledgeChunk.job_id == job_id, RagKnowledgeChunkImage.oss_key != "")
            )
        ).all()
        return [row for row in rows if row]

    async def get_oss_keys_by_file_id(self, file_id: str) -> list[str]:
        rows = (
            await self.session.scalars(
                select(RagKnowledgeChunkImage.oss_key)
                .join(RagKnowledgeChunk, RagKnowledgeChunk.id == RagKnowledgeChunkImage.chunk_id)
                .join(RagKnowledgeJob, RagKnowledgeJob.id == RagKnowledgeChunk.job_id)
                .where(RagKnowledgeJob.file_id == file_id, RagKnowledgeChunkImage.oss_key != "")
            )
        ).all()
        return [row for row in rows if row]

    async def delete(self, record_id: str) -> None:
        await self.session.execute(delete(RagKnowledgeChunkImage).where(RagKnowledgeChunkImage.id == record_id))

    async def delete_by_chunk(self, chunk_id: str) -> None:
        await self.session.execute(delete(RagKnowledgeChunkImage).where(RagKnowledgeChunkImage.chunk_id == chunk_id))

    async def delete_by_job(self, job_id: str) -> None:
        chunk_ids = select(RagKnowledgeChunk.id).where(RagKnowledgeChunk.job_id == job_id)
        await self.session.execute(delete(RagKnowledgeChunkImage).where(RagKnowledgeChunkImage.chunk_id.in_(chunk_ids)))

    @staticmethod
    def _normalize(row: RagKnowledgeChunkImage) -> dict[str, Any]:
        return {
            "id": row.id,
            "chunk_id": row.chunk_id,
            "placeholder": row.placeholder,
            "oss_key": row.oss_key,
            "oss_url": "",
            "page": row.page,
            "sort_order": row.sort_order,
            "created_at": _dt(row.created_at),
        }


class ConversationRepository(BaseRepository):
    async def create_session(self, *, kb_name: str, user_id: str = "default", title: str = "New conversation") -> dict[str, Any]:
        row = RagConversationSession(kb_name=kb_name, user_id=user_id, title=title)
        self.session.add(row)
        await self.flush_refresh(row)
        return self._norm_session(row)

    async def get_session(self, session_id: str) -> dict[str, Any] | None:
        row = await self.session.get(RagConversationSession, session_id)
        return self._norm_session(row) if row else None

    async def list_sessions(self, kb_name: str, user_id: str = "default") -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(RagConversationSession, func.count(RagConversationMessage.id).label("message_count"))
                .join(RagConversationMessage, RagConversationMessage.session_id == RagConversationSession.id, isouter=True)
                .where(RagConversationSession.user_id == user_id, RagConversationSession.kb_name == kb_name)
                .group_by(RagConversationSession.id)
                .order_by(RagConversationSession.updated_at.desc())
            )
        ).all()
        return [self._norm_session(row[0], message_count=row.message_count) for row in rows]

    async def touch_session(self, session_id: str) -> None:
        await self.session.execute(update(RagConversationSession).where(RagConversationSession.id == session_id).values(updated_at=func.now()))

    async def delete_session(self, session_id: str) -> None:
        await self.session.execute(delete(RagConversationSession).where(RagConversationSession.id == session_id))

    async def add_message(self, **values) -> dict[str, Any]:
        row = RagConversationMessage(
            session_id=values["session_id"],
            role=values["role"],
            content=values["content"],
            sources=values.get("sources") or [],
            confidence=values.get("confidence"),
            image_placeholders=values.get("image_placeholders") or [],
            query_image_oss_key=values.get("query_image_oss_key"),
        )
        self.session.add(row)
        await self.flush_refresh(row)
        return self._norm_message(row)

    async def list_messages(self, session_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = (
            await self.session.scalars(
                select(RagConversationMessage)
                .where(RagConversationMessage.session_id == session_id)
                .order_by(RagConversationMessage.created_at.asc())
                .limit(limit)
            )
        ).all()
        return [self._norm_message(row) for row in rows]

    async def get_image_placeholders_by_session(self, session_id: str) -> list[str]:
        rows = (
            await self.session.scalars(
                select(RagConversationMessage.image_placeholders).where(RagConversationMessage.session_id == session_id)
            )
        ).all()
        result: set[str] = set()
        for placeholders in rows:
            result.update(placeholders or [])
        return list(result)

    @staticmethod
    def _norm_session(row: RagConversationSession, *, message_count: int = 0) -> dict[str, Any]:
        return {
            "id": row.id,
            "user_id": row.user_id,
            "kb_name": row.kb_name,
            "title": row.title,
            "message_count": int(message_count),
            "created_at": _dt(row.created_at),
            "updated_at": _dt(row.updated_at),
        }

    @staticmethod
    def _norm_message(row: RagConversationMessage) -> dict[str, Any]:
        return {
            "id": row.id,
            "session_id": row.session_id,
            "role": row.role,
            "content": row.content,
            "sources": row.sources or [],
            "confidence": row.confidence,
            "image_placeholders": row.image_placeholders or [],
            "query_image_oss_key": row.query_image_oss_key,
            "created_at": _dt(row.created_at),
        }


def get_kb_repository(session: AsyncSession) -> KbRepository:
    return KbRepository(session)


def get_category_repository(session: AsyncSession) -> CategoryRepository:
    return CategoryRepository(session)


def get_category_file_repository(session: AsyncSession) -> CategoryFileRepository:
    return CategoryFileRepository(session)


def get_file_repository(session: AsyncSession) -> FileRepository:
    return FileRepository(session)


def get_job_repository(session: AsyncSession) -> JobRepository:
    return JobRepository(session)


def get_chunk_repository(session: AsyncSession) -> ChunkRepository:
    return ChunkRepository(session)


def get_chunk_image_repository(session: AsyncSession) -> ChunkImageRepository:
    return ChunkImageRepository(session)


def get_conversation_repository(session: AsyncSession) -> ConversationRepository:
    return ConversationRepository(session)

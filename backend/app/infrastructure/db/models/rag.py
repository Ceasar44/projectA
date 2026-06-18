import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.infrastructure.db.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class RagKnowledgeBase(Base):
    __tablename__ = "knowledge_base"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    display_name: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    image_mode: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    embedding_model: Mapped[str] = mapped_column(Text, nullable=False, default="text-embedding-v3")
    vector_dim: Mapped[int] = mapped_column(Integer, nullable=False, default=1536)
    metadata_fields: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    retrieval_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    kb_type: Mapped[str] = mapped_column(Text, nullable=False, default="standard")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    files: Mapped[list["RagKnowledgeFile"]] = relationship(back_populates="knowledge_base")
    jobs: Mapped[list["RagKnowledgeJob"]] = relationship(back_populates="knowledge_base")


class RagKnowledgeCategory(Base):
    __tablename__ = "knowledge_category"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    files: Mapped[list["RagKnowledgeCategoryFile"]] = relationship(back_populates="category")


class RagKnowledgeCategoryFile(Base):
    __tablename__ = "knowledge_category_file"
    __table_args__ = (UniqueConstraint("category_id", "file_name", name="uq_rag_category_file_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    category_id: Mapped[str] = mapped_column(ForeignKey("knowledge_category.id", ondelete="CASCADE"), index=True)
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    oss_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    category: Mapped[RagKnowledgeCategory] = relationship(back_populates="files")
    knowledge_files: Mapped[list["RagKnowledgeFile"]] = relationship(back_populates="category_file")


class RagKnowledgeFile(Base):
    __tablename__ = "knowledge_file"
    __table_args__ = (UniqueConstraint("kb_id", "oss_key", name="uq_rag_knowledge_file_oss_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    kb_id: Mapped[str] = mapped_column(ForeignKey("knowledge_base.id", ondelete="CASCADE"), index=True)
    category_file_id: Mapped[str | None] = mapped_column(
        ForeignKey("knowledge_category_file.id", ondelete="SET NULL")
    )
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    oss_key: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending", index=True)
    error_msg: Mapped[str | None] = mapped_column(Text)
    sync_graph: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    knowledge_base: Mapped[RagKnowledgeBase] = relationship(back_populates="files")
    category_file: Mapped[RagKnowledgeCategoryFile | None] = relationship(back_populates="knowledge_files")
    jobs: Mapped[list["RagKnowledgeJob"]] = relationship(back_populates="file")


class RagKnowledgeJob(Base):
    __tablename__ = "knowledge_job"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    file_id: Mapped[str] = mapped_column(ForeignKey("knowledge_file.id", ondelete="CASCADE"), index=True)
    kb_id: Mapped[str] = mapped_column(ForeignKey("knowledge_base.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="pending", index=True)
    stage: Mapped[str | None] = mapped_column(Text)
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunk_count: Mapped[int | None] = mapped_column(Integer)
    vectorized: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_msg: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    file: Mapped[RagKnowledgeFile] = relationship(back_populates="jobs")
    knowledge_base: Mapped[RagKnowledgeBase] = relationship(back_populates="jobs")
    chunks: Mapped[list["RagKnowledgeChunk"]] = relationship(back_populates="job")


class RagKnowledgeChunk(Base):
    __tablename__ = "knowledge_chunk"
    __table_args__ = (UniqueConstraint("job_id", "chunk_index", name="uq_rag_chunk_job_index"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    job_id: Mapped[str] = mapped_column(ForeignKey("knowledge_job.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_modified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, nullable=False, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    job: Mapped[RagKnowledgeJob] = relationship(back_populates="chunks")
    origin: Mapped["RagKnowledgeChunkOrigin"] = relationship(back_populates="chunk", uselist=False)
    images: Mapped[list["RagKnowledgeChunkImage"]] = relationship(back_populates="chunk")


class RagKnowledgeChunkOrigin(Base):
    __tablename__ = "knowledge_chunk_origin"

    chunk_id: Mapped[str] = mapped_column(
        ForeignKey("knowledge_chunk.id", ondelete="CASCADE"), primary_key=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    chunk: Mapped[RagKnowledgeChunk] = relationship(back_populates="origin")


class RagKnowledgeChunkImage(Base):
    __tablename__ = "knowledge_chunk_image"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    chunk_id: Mapped[str] = mapped_column(ForeignKey("knowledge_chunk.id", ondelete="CASCADE"), index=True)
    placeholder: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    oss_key: Mapped[str] = mapped_column(Text, nullable=False)
    page: Mapped[int | None] = mapped_column(Integer)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    chunk: Mapped[RagKnowledgeChunk] = relationship(back_populates="images")


class RagConversationSession(Base):
    __tablename__ = "conversation_session"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(Text, nullable=False, default="default")
    kb_name: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="New conversation")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["RagConversationMessage"]] = relationship(back_populates="session")


class RagConversationMessage(Base):
    __tablename__ = "conversation_message"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("conversation_session.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list | None] = mapped_column(JSON)
    confidence: Mapped[float | None] = mapped_column(Float)
    image_placeholders: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    query_image_oss_key: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    session: Mapped[RagConversationSession] = relationship(back_populates="messages")

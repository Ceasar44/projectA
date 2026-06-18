from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.rag.core.exceptions import ConflictError, NotFoundError
from app.rag.db import get_file_repository, get_kb_repository
from app.rag.services.milvus_service import get_milvus_service

router = APIRouter(prefix="/collections", tags=["rag-admin-collections"])


class MetadataFieldConfig(BaseModel):
    key: str
    type: str = "text"
    fulltext: bool = False
    index: bool = False
    auto_inject: Optional[str] = None


class RetrievalConfig(BaseModel):
    ranker: str = "RRF"
    rrf_k: int = 60
    hybrid_alpha: float = 0.5
    multi_doc_top_k: int = 20
    multi_doc_group_size: int = 3
    strict_group_size: bool = False
    single_doc_top_k: int = 20
    llm_context_top_k: int = 10
    image_vector_dim: int = 1024
    rerank_enabled: bool = False
    rerank_model_name: str = "qwen3-rerank"
    single_doc_rerank_top_k: int = 5
    multi_doc_rerank_top_k: int = 10


class CreateKbRequest(BaseModel):
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    image_mode: bool = False
    kb_type: str = "standard"
    embedding_model: str = "text-embedding-v3"
    vector_dim: int = 1536
    metadata_fields: Optional[list[MetadataFieldConfig]] = None
    retrieval_config: Optional[RetrievalConfig] = None


class UpdateKbRequest(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    image_mode: Optional[bool] = None
    retrieval_config: Optional[RetrievalConfig] = None


@router.get("")
async def list_collections(session: AsyncSession = Depends(get_session)):
    collections = await get_kb_repository(session).list_all()
    return {"success": True, "data": {"collections": collections, "total": len(collections)}}


@router.post("")
async def create_collection(req: CreateKbRequest, session: AsyncSession = Depends(get_session)):
    kb_repo = get_kb_repository(session)
    if await kb_repo.get_by_name(req.name):
        raise ConflictError(f"Knowledge base already exists: {req.name}")

    metadata_fields = [field.model_dump() for field in req.metadata_fields] if req.metadata_fields else []
    retrieval_config = req.retrieval_config.model_dump() if req.retrieval_config else {}
    embedding_model = req.embedding_model
    vector_dim = req.vector_dim

    if req.kb_type == "multimodal":
        embedding_model = "qwen3-vl-embedding"
        vector_dim = retrieval_config.get("image_vector_dim", 1024)
        retrieval_config["image_vector_dim"] = vector_dim

    get_milvus_service().get_or_create_collection(
        collection_name=req.name,
        dim=vector_dim,
        image_mode=req.image_mode,
        metadata_fields=metadata_fields,
        kb_type=req.kb_type,
        image_vector_dim=retrieval_config.get("image_vector_dim", 1024),
    )

    kb = await kb_repo.create(
        name=req.name,
        display_name=req.display_name,
        description=req.description,
        image_mode=req.image_mode,
        kb_type=req.kb_type,
        embedding_model=embedding_model,
        vector_dim=vector_dim,
        metadata_fields=metadata_fields,
        retrieval_config=retrieval_config,
    )
    await session.commit()
    return {"success": True, "message": f"Knowledge base {req.name} created", "data": kb}


@router.get("/{kb_name}")
async def get_collection(kb_name: str, session: AsyncSession = Depends(get_session)):
    kb = await get_kb_repository(session).get_by_name(kb_name)
    if not kb:
        raise NotFoundError(f"Knowledge base not found: {kb_name}")
    return {"success": True, "data": kb}


@router.put("/{kb_name}")
async def update_collection(
    kb_name: str,
    req: UpdateKbRequest,
    session: AsyncSession = Depends(get_session),
):
    kb_repo = get_kb_repository(session)
    kb = await kb_repo.get_by_name(kb_name)
    if not kb:
        raise NotFoundError(f"Knowledge base not found: {kb_name}")
    updated = await kb_repo.update(
        kb["id"],
        display_name=req.display_name,
        description=req.description,
        image_mode=req.image_mode,
        retrieval_config=req.retrieval_config.model_dump() if req.retrieval_config else None,
    )
    await session.commit()
    return {"success": True, "data": updated}


@router.delete("/{kb_name}")
async def delete_collection(kb_name: str, session: AsyncSession = Depends(get_session)):
    kb_repo = get_kb_repository(session)
    kb = await kb_repo.get_by_name(kb_name)
    if not kb:
        raise NotFoundError(f"Knowledge base not found: {kb_name}")
    files = await get_file_repository(session).list_by_kb(kb["id"], limit=1)
    if files:
        raise ConflictError("Delete all files in this knowledge base first")
    try:
        get_milvus_service().delete_collection(kb_name)
    except Exception:
        pass
    await kb_repo.delete(kb["id"])
    await session.commit()
    return {"success": True, "message": f"Knowledge base {kb_name} deleted"}

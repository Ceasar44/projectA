import json

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.rag.services import document_service
from app.rag.services.oss_service import get_oss_service

router = APIRouter(prefix="/documents", tags=["rag-documents"])


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    kb_name: str = Form(...),
    chunk_size: int = Form(500),
    chunk_overlap: int = Form(50),
    image_dpi: int = Form(150),
    sync_graph: bool = Form(False, description="Sync chunks to knowledge graph"),
    session: AsyncSession = Depends(get_session),
):
    result = await document_service.upload_document(
        session=session,
        file_name=file.filename,
        file_content=await file.read(),
        kb_name=kb_name,
        background_tasks=background_tasks,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        image_dpi=image_dpi,
        sync_graph=sync_graph,
    )
    return {"success": True, "message": "Upload submitted", "data": result}


@router.post("/upload-to-category")
async def upload_document_to_category(
    file: UploadFile = File(...),
    category_id: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    record = await document_service.upload_to_category(
        session=session,
        file_name=file.filename,
        file_content=await file.read(),
        category_id=category_id,
    )
    await session.commit()
    return {"success": True, "message": "File uploaded to category", "data": record}


@router.post("/batch-upload-to-category")
async def batch_upload_to_category(
    files: list[UploadFile] = File(...),
    category_id: str = Form(...),
    session: AsyncSession = Depends(get_session),
):
    file_pairs = [(item.filename, await item.read()) for item in files]
    result = await document_service.batch_upload_to_category(session, file_pairs, category_id)
    await session.commit()
    return {
        "success": True,
        "message": f"Uploaded {len(result['succeeded'])}; failed {len(result['failed'])}",
        "data": result,
    }


@router.get("/excel-columns")
async def get_excel_columns(
    category_file_id: str = Query(..., description="Category file ID"),
    session: AsyncSession = Depends(get_session),
):
    result = await document_service.get_excel_columns(session, category_file_id)
    return {"success": True, "data": result}


@router.post("/start-chunking-excel/{category_id}")
async def start_chunking_excel(
    category_id: str,
    background_tasks: BackgroundTasks,
    kb_name: str = Query(..., description="Target knowledge base name"),
    excel_rows_per_chunk: int = Query(50),
    excel_configs: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
):
    configs = json.loads(excel_configs) if excel_configs else None
    result = await document_service.start_chunking_excel(
        session=session,
        category_id=category_id,
        kb_name=kb_name,
        background_tasks=background_tasks,
        excel_rows_per_chunk=excel_rows_per_chunk,
        excel_configs=configs,
    )
    return {"success": True, "message": f"Submitted {result['submitted']} Excel files", "data": result}


@router.post("/start-chunking/{category_id}")
async def start_chunking(
    category_id: str,
    background_tasks: BackgroundTasks,
    kb_name: str = Query(..., description="Target knowledge base name"),
    chunk_size: int = Query(500),
    chunk_overlap: int = Query(50),
    image_dpi: int = Query(150),
    sync_graph: bool = Query(False),
    excel_rows_per_chunk: int = Query(50),
    session: AsyncSession = Depends(get_session),
):
    result = await document_service.start_chunking(
        session=session,
        category_id=category_id,
        kb_name=kb_name,
        background_tasks=background_tasks,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        image_dpi=image_dpi,
        sync_graph=sync_graph,
        excel_rows_per_chunk=excel_rows_per_chunk,
    )
    return {"success": True, "message": f"Submitted {result['submitted']} files", "data": result}


@router.post("/search")
async def search_documents(
    query: str = Form(...),
    kb_name: str | None = Form(None),
    collection: str | None = Form(None),
    top_k: int = Form(10),
    filter_expr: str | None = Form(None),
    hybrid_search: str | None = Form(None),
    hybrid_alpha: float = Form(0.5),
    keyword_filter: str | None = Form(None),
    rerank: bool = Form(False),
    rerank_model: str = Form("qwen3-rerank"),
    rerank_top_n: int | None = Form(None),
    session: AsyncSession = Depends(get_session),
):
    kb = kb_name or collection
    if not kb:
        return {"detail": "kb_name or collection is required"}
    results = await document_service.search_documents(
        session=session,
        query=query,
        kb_name=kb,
        top_k=top_k,
        filter_expr=filter_expr or None,
        ranker=hybrid_search or "RRF",
        hybrid_alpha=hybrid_alpha,
        keyword_filter=keyword_filter or None,
        rerank=rerank,
        rerank_model=rerank_model,
        rerank_top_n=rerank_top_n,
    )
    return {"success": True, "data": {"query": query, "results": results, "total": len(results)}}


@router.get("/image-proxy")
async def image_proxy(oss_key: str):
    data = get_oss_service().get_object_bytes(oss_key)
    ext = oss_key.rsplit(".", 1)[-1].lower() if "." in oss_key else "png"
    content_type = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
    }.get(ext, "image/png")
    return Response(content=data, media_type=content_type)

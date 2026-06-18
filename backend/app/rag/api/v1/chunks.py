from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.rag.services import chunk_service

router = APIRouter(prefix="/chunks", tags=["rag-chunks"])


class EditChunkBody(BaseModel):
    content: str


class BatchCleanBody(BaseModel):
    instruction: str | None = None


class BatchUpsertRequest(BaseModel):
    job_ids: list[str]


class ResolveImagesRequest(BaseModel):
    placeholders: list[str]


class ResolveOssKeysRequest(BaseModel):
    oss_keys: list[str]


@router.get("/job/{job_id}")
async def get_chunks_by_job(job_id: str, session: AsyncSession = Depends(get_session)):
    return {"success": True, "data": await chunk_service.get_chunks_by_job(session, job_id)}


@router.put("/job/{job_id}/chunk/{chunk_index}")
async def edit_chunk(
    job_id: str,
    chunk_index: int,
    body: EditChunkBody,
    session: AsyncSession = Depends(get_session),
):
    await chunk_service.edit_chunk(session, job_id, chunk_index, body.content)
    await session.commit()
    return {"success": True, "message": "Chunk updated"}


@router.post("/job/{job_id}/chunk/{chunk_index}/clean")
async def clean_single_chunk(
    job_id: str,
    chunk_index: int,
    instruction: str | None = Form(None),
    session: AsyncSession = Depends(get_session),
):
    cleaned = await chunk_service.clean_single_chunk(session, job_id, chunk_index, instruction)
    await session.commit()
    return {"success": True, "message": "Chunk cleaned", "data": {"content": cleaned}}


@router.post("/job/{job_id}/chunk/{chunk_index}/revert")
async def revert_single_chunk(job_id: str, chunk_index: int, session: AsyncSession = Depends(get_session)):
    await chunk_service.revert_single_chunk(session, job_id, chunk_index)
    await session.commit()
    return {"success": True, "message": "Chunk reverted"}


@router.post("/job/{job_id}/clean")
async def clean_job_chunks(
    job_id: str,
    body: BatchCleanBody = BatchCleanBody(),
    session: AsyncSession = Depends(get_session),
):
    result = await chunk_service.clean_job_chunks(session, job_id, body.instruction)
    await session.commit()
    return {"success": True, "message": f"Cleaned {result['success']}/{result['total']} chunks", "data": result}


@router.post("/job/{job_id}/revert")
async def revert_job_chunks(job_id: str, session: AsyncSession = Depends(get_session)):
    await chunk_service.revert_job_chunks(session, job_id)
    await session.commit()
    return {"success": True, "message": "Job chunks reverted"}


@router.post("/clean-all")
async def clean_all_chunks(
    body: BatchCleanBody = BatchCleanBody(),
    session: AsyncSession = Depends(get_session),
):
    result = await chunk_service.clean_all_chunks(session, body.instruction)
    await session.commit()
    return {"success": True, "message": f"Cleaned {result['success']}; failed {result['failed']}", "data": result}


@router.post("/revert-all")
async def revert_all_chunks(session: AsyncSession = Depends(get_session)):
    await chunk_service.revert_all_chunks(session)
    await session.commit()
    return {"success": True, "message": "All chunks reverted"}


@router.post("/job/{job_id}/upsert")
async def upsert_job_chunks(job_id: str, session: AsyncSession = Depends(get_session)):
    result = await chunk_service.upsert_job_chunks(session, job_id)
    await session.commit()
    return {"success": True, "message": "Upsert complete", "data": result}


@router.post("/batch-upsert")
async def batch_upsert_jobs(body: BatchUpsertRequest, session: AsyncSession = Depends(get_session)):
    result = await chunk_service.batch_upsert_jobs(session, body.job_ids)
    await session.commit()
    return {
        "success": True,
        "message": f"Upserted {len(result['succeeded'])}; failed {len(result['failed'])}",
        "data": result,
    }


@router.get("/job/{job_id}/chunk/{chunk_index}/images")
async def get_chunk_images(job_id: str, chunk_index: int, session: AsyncSession = Depends(get_session)):
    images = await chunk_service.get_chunk_images(session, job_id, chunk_index)
    return {"success": True, "data": {"images": images}}


@router.post("/job/{job_id}/chunk/{chunk_index}/images")
async def add_chunk_image(
    job_id: str,
    chunk_index: int,
    file: UploadFile = File(...),
    page: int | None = Form(None),
    insert_position: int = Form(0),
    session: AsyncSession = Depends(get_session),
):
    record = await chunk_service.add_chunk_image(
        session=session,
        job_id=job_id,
        chunk_index=chunk_index,
        file_content=await file.read(),
        filename=file.filename,
        insert_position=insert_position,
        page=page,
    )
    await session.commit()
    return {"success": True, "data": record}


@router.delete("/job/{job_id}/chunk/{chunk_index}/images/{image_id}")
async def delete_chunk_image(
    job_id: str,
    chunk_index: int,
    image_id: str,
    session: AsyncSession = Depends(get_session),
):
    await chunk_service.delete_chunk_image(session, job_id, chunk_index, image_id)
    await session.commit()
    return {"success": True, "message": "Image deleted"}


@router.post("/resolve-images")
async def resolve_images(body: ResolveImagesRequest, session: AsyncSession = Depends(get_session)):
    result = await chunk_service.resolve_image_placeholders(session, body.placeholders)
    return {"success": True, "data": result}


@router.post("/resolve-oss-keys")
async def resolve_oss_keys(body: ResolveOssKeysRequest):
    from app.rag.services.oss_service import get_oss_service

    oss_service = get_oss_service()
    result = {}
    for key in body.oss_keys:
        if key:
            try:
                result[key] = oss_service.get_presigned_url(key, expires=3600)
            except Exception:
                pass
    return {"success": True, "data": result}

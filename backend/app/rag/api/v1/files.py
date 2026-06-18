from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.rag.services import file_service

router = APIRouter(prefix="/files", tags=["rag-files"])


class DeleteFileRequest(BaseModel):
    file_id: str


class BatchDeleteFilesRequest(BaseModel):
    file_ids: list[str]
    kb_name: str


@router.get("")
async def list_files(
    kb_name: str = Query(..., description="Knowledge base name"),
    limit: int = Query(default=200, ge=1, le=2000),
    session: AsyncSession = Depends(get_session),
):
    result = await file_service.list_files(session, kb_name=kb_name, limit=limit)
    return {"success": True, "data": result}


@router.delete("")
async def delete_file(req: DeleteFileRequest, session: AsyncSession = Depends(get_session)):
    file_name = await file_service.delete_file(session, req.file_id)
    await session.commit()
    return {"success": True, "message": f"File {file_name} deleted"}


@router.post("/batch-delete")
async def batch_delete_files(req: BatchDeleteFilesRequest, session: AsyncSession = Depends(get_session)):
    result = await file_service.batch_delete_files(session, req.file_ids, req.kb_name)
    await session.commit()
    return {
        "success": True,
        "message": f"Deleted {len(result['deleted'])}; failed {len(result['failed'])}",
        "data": result,
    }

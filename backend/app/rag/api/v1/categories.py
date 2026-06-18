from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.rag.services import category_service

router = APIRouter(prefix="/categories", tags=["rag-categories"])


class CategoryCreate(BaseModel):
    name: str
    description: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class BatchDeleteFilesRequest(BaseModel):
    file_ids: list[str]


@router.get("")
async def list_categories(session: AsyncSession = Depends(get_session)):
    return {"success": True, "data": await category_service.list_categories(session)}


@router.post("")
async def create_category(body: CategoryCreate, session: AsyncSession = Depends(get_session)):
    category = await category_service.create_category(session, body.name, body.description)
    await session.commit()
    return {"success": True, "message": "Category created", "data": category}


@router.get("/{category_id}")
async def get_category(category_id: str, session: AsyncSession = Depends(get_session)):
    result = await category_service.get_category_with_files(session, category_id)
    return {"success": True, "data": result}


@router.put("/{category_id}")
async def update_category(
    category_id: str,
    body: CategoryUpdate,
    session: AsyncSession = Depends(get_session),
):
    result = await category_service.update_category(session, category_id, body.name, body.description)
    await session.commit()
    return {"success": True, "message": "Category updated", "data": result}


@router.delete("/{category_id}")
async def delete_category(category_id: str, session: AsyncSession = Depends(get_session)):
    await category_service.delete_category(session, category_id)
    await session.commit()
    return {"success": True, "message": "Category deleted"}


@router.delete("/{category_id}/files/{file_id}")
async def delete_category_file(
    category_id: str,
    file_id: str,
    session: AsyncSession = Depends(get_session),
):
    file_name = await category_service.delete_category_file(session, category_id, file_id)
    await session.commit()
    return {"success": True, "message": f"File {file_name} deleted"}


@router.post("/{category_id}/files/batch-delete")
async def batch_delete_category_files(
    category_id: str,
    body: BatchDeleteFilesRequest,
    session: AsyncSession = Depends(get_session),
):
    result = await category_service.batch_delete_category_files(session, category_id, body.file_ids)
    await session.commit()
    return JSONResponse(
        content={
            "success": True,
            "message": f"Deleted {len(result['deleted'])} files",
            "data": result,
        }
    )

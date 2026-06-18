from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import ORJSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.compat import isoformat
from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.domain.knowledge.schemas import (
    CategoryCreate,
    EntryCreate,
)
from app.domain.knowledge.service import KnowledgeService
from app.infrastructure.db.models.knowledge import Category, KnowledgeEntry
from app.infrastructure.db.models.operations import Settings
from app.infrastructure.db.repositories.knowledge import CategoryRepository, KnowledgeEntryRepository
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter()


def build_service(session: AsyncSession) -> KnowledgeService:
    return KnowledgeService(
        category_repo=CategoryRepository(session),
        entry_repo=KnowledgeEntryRepository(session),
        uow=SQLAlchemyUnitOfWork(session),
    )


def serialize_category(category: Category) -> dict[str, object]:
    return {
        "id": category.id,
        "name": category.name,
        "description": category.description,
        "icon": category.icon,
        "color": category.color,
        "sortOrder": category.sort_order,
        "_count": {"entries": len(category.entries)},
        "createdAt": isoformat(category.created_at),
        "updatedAt": isoformat(category.updated_at),
    }


def serialize_entry(entry: KnowledgeEntry) -> dict[str, object]:
    return {
        "id": entry.id,
        "categoryId": entry.category_id,
        "category": {
            "id": entry.category.id,
            "name": entry.category.name,
            "color": entry.category.color,
            "icon": entry.category.icon,
        } if entry.category else None,
        "title": entry.title,
        "content": entry.content,
        "priority": entry.priority,
        "isActive": entry.is_active,
        "version": entry.version,
        "createdAt": isoformat(entry.created_at),
        "updatedAt": isoformat(entry.updated_at),
    }


@router.get("/categories")
async def list_categories(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    response = await build_service(session).list_categories(page, limit)
    return {
        "data": [
            serialize_category(
                await session.scalar(
                    select(Category).options(selectinload(Category.entries)).where(Category.id == item.id)
                )
            )
            for item in response.data
        ],
        "pagination": {
            "page": response.pagination.page,
            "limit": response.pagination.limit,
            "total": response.pagination.total,
            "totalPages": response.pagination.total_pages,
        },
    }


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: dict[str, object],
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    name = str(payload.get("name", "")).strip()
    if not name:
        return ORJSONResponse({"error": "Category name is required"}, status_code=400)

    max_sort = await session.scalar(select(Category.sort_order).order_by(Category.sort_order.desc()).limit(1))
    normalized = {
        **payload,
        "name": name,
        "description": str(payload.get("description", "")).strip(),
        "icon": payload.get("icon") or "folder",
        "color": payload.get("color") or "#4A7C9B",
        "sortOrder": payload.get("sortOrder", (max_sort or -1) + 1),
    }
    created = await build_service(session).create_category(CategoryCreate.model_validate(normalized))
    category = await session.scalar(select(Category).options(selectinload(Category.entries)).where(Category.id == created.id))
    return serialize_category(category)


@router.put("/categories/{category_id}")
async def update_category(
    category_id: str,
    payload: dict,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    category = await session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    update_payload = CategoryCreate(
        name=payload.get("name", category.name),
        description=payload.get("description", category.description),
        icon=payload.get("icon", category.icon),
        color=payload.get("color", category.color),
        sortOrder=payload.get("sortOrder", category.sort_order),
    )
    await build_service(session).update_category(category_id, update_payload)
    category = await session.scalar(select(Category).options(selectinload(Category.entries)).where(Category.id == category_id))
    return serialize_category(category)


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    category = await session.scalar(
        select(Category).options(selectinload(Category.entries)).where(Category.id == category_id)
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    if category.entries:
        return ORJSONResponse(
            {"error": "Please delete all entries in this category before deleting the category."},
            status_code=400,
        )
    return await build_service(session).delete_category(category_id)


@router.get("/entries")
async def list_entries(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    category_id: str | None = Query(default=None, alias="categoryId"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    response = await build_service(session).list_entries(page, limit, category_id)
    return {
        "data": [
            serialize_entry(
                await session.scalar(
                    select(KnowledgeEntry)
                    .options(selectinload(KnowledgeEntry.category))
                    .where(KnowledgeEntry.id == item.id)
                )
            )
            for item in response.data
        ],
        "pagination": {
            "page": response.pagination.page,
            "limit": response.pagination.limit,
            "total": response.pagination.total,
            "totalPages": response.pagination.total_pages,
        },
    }


@router.post("/entries", status_code=status.HTTP_201_CREATED)
async def create_entry(
    payload: dict[str, object],
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    category_id = str(payload.get("categoryId", "")).strip()
    title = str(payload.get("title", "")).strip()
    if not category_id:
        return ORJSONResponse({"error": "Category ID is required"}, status_code=400)
    if not title:
        return ORJSONResponse({"error": "Title is required"}, status_code=400)
    category = await session.get(Category, category_id)
    if not category:
        return ORJSONResponse({"error": "Category not found"}, status_code=404)
    normalized = {
        **payload,
        "categoryId": category_id,
        "title": title,
        "content": str(payload.get("content", "")).strip(),
        "priority": payload.get("priority", 0),
    }
    created = await build_service(session).create_entry(EntryCreate.model_validate(normalized))
    entry = await session.scalar(select(KnowledgeEntry).options(selectinload(KnowledgeEntry.category)).where(KnowledgeEntry.id == created.id))
    return serialize_entry(entry)


@router.put("/entries/{entry_id}")
async def update_entry(
    entry_id: str,
    payload: dict,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    entry = await session.get(KnowledgeEntry, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    update_payload = EntryCreate(
        categoryId=payload.get("categoryId", entry.category_id),
        title=payload.get("title", entry.title),
        content=payload.get("content", entry.content),
        priority=payload.get("priority", entry.priority),
        isActive=payload.get("isActive", entry.is_active),
    )
    await build_service(session).update_entry(entry_id, update_payload)
    entry = await session.scalar(select(KnowledgeEntry).options(selectinload(KnowledgeEntry.category)).where(KnowledgeEntry.id == entry_id))
    return serialize_entry(entry)


@router.delete("/entries/{entry_id}")
async def delete_entry(
    entry_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    return await build_service(session).delete_entry(entry_id)


@router.post("/test")
async def knowledge_test(
    payload: dict,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    question = str(payload.get("question", "")).strip()
    if not question:
        return ORJSONResponse({"error": "Question is required"}, status_code=400)

    settings = await session.scalar(select(Settings).where(Settings.id == "default"))
    if not settings or not settings.ai_api_key:
        return ORJSONResponse(
            {"error": "AI API key is not configured. Please configure it in Settings."},
            status_code=400,
        )

    entries = list(
        (
            await session.scalars(
                select(KnowledgeEntry)
                .options(selectinload(KnowledgeEntry.category))
                .where(KnowledgeEntry.is_active.is_(True))
                .order_by(KnowledgeEntry.priority.desc(), KnowledgeEntry.updated_at.desc())
            )
        ).all()
    )
    if not entries:
        return ORJSONResponse(
            {"error": "No active knowledge base entries found. Add entries first."},
            status_code=400,
        )

    top_entries = entries[:3]
    sources = [
        {
            "id": entry.id,
            "title": entry.title,
            "category": entry.category.name if entry.category else "",
            "categoryColor": entry.category.color if entry.category else "",
            "contentPreview": entry.content[:200],
        }
        for entry in top_entries
    ]
    answer = "\n\n".join(
        f"{entry.title}: {entry.content[:280].strip()}" for entry in top_entries
    )
    return {
        "answer": answer or "No answer available.",
        "sources": sources,
        "model": settings.ai_model or "gpt-4o-mini",
        "totalEntries": len(entries),
    }

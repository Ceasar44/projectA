from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.compat import isoformat
from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.domain.operations.schemas import (
    BusinessHoursRead,
    BusinessHoursUpdate,
    CannedResponseCreate,
    CannedResponseUpdate,
    SLARuleCreate,
    SLARuleUpdate,
)
from app.domain.operations.service import OperationsService
from app.infrastructure.db.repositories.operations import OperationsRepository
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter()


def build_service(session: AsyncSession) -> OperationsService:
    return OperationsService(OperationsRepository(session), SQLAlchemyUnitOfWork(session))


@router.get("/business-hours", response_model=BusinessHoursRead)
async def get_business_hours(
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> BusinessHoursRead:
    return await build_service(session).get_business_hours()


@router.put("/business-hours", response_model=BusinessHoursRead)
async def update_business_hours(
    payload: BusinessHoursUpdate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> BusinessHoursRead:
    return await build_service(session).update_business_hours(payload)


@router.get("/sla")
async def list_sla(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    response = await build_service(session).list_sla(page, limit)
    return [
        {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "channel": item.channel,
            "priority": item.priority,
            "firstResponseMins": item.first_response_mins,
            "resolutionMins": item.resolution_mins,
            "isActive": item.is_active,
            "createdAt": isoformat(item.created_at),
            "updatedAt": isoformat(item.updated_at),
        }
        for item in response.data
    ]


@router.post("/sla", status_code=status.HTTP_201_CREATED)
async def create_sla(
    payload: SLARuleCreate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    item = await build_service(session).create_sla(payload)
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "channel": item.channel,
        "priority": item.priority,
        "firstResponseMins": item.first_response_mins,
        "resolutionMins": item.resolution_mins,
        "isActive": item.is_active,
        "createdAt": isoformat(item.created_at),
        "updatedAt": isoformat(item.updated_at),
    }


@router.put("/sla/{rule_id}")
async def update_sla(
    rule_id: str,
    payload: SLARuleUpdate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    item = await build_service(session).update_sla(rule_id, payload)
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "channel": item.channel,
        "priority": item.priority,
        "firstResponseMins": item.first_response_mins,
        "resolutionMins": item.resolution_mins,
        "isActive": item.is_active,
        "createdAt": isoformat(item.created_at),
        "updatedAt": isoformat(item.updated_at),
    }


@router.delete("/sla/{rule_id}")
async def delete_sla(
    rule_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    return await build_service(session).delete_sla(rule_id)


@router.get("/canned-responses")
async def list_canned(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    category: str | None = None,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    response = await build_service(session).list_canned(page, limit)
    items = response.data
    if category:
        items = [item for item in items if item.category == category]
    return [
        {
            "id": item.id,
            "title": item.title,
            "content": item.content,
            "category": item.category,
            "shortcut": item.shortcut,
            "isActive": item.is_active,
            "usageCount": item.usage_count,
            "createdAt": isoformat(item.created_at),
            "updatedAt": isoformat(item.updated_at),
        }
        for item in items
    ]


@router.post("/canned-responses", status_code=status.HTTP_201_CREATED)
async def create_canned(
    payload: CannedResponseCreate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    item = await build_service(session).create_canned(payload)
    return {
        "id": item.id,
        "title": item.title,
        "content": item.content,
        "category": item.category,
        "shortcut": item.shortcut,
        "isActive": item.is_active,
        "usageCount": item.usage_count,
        "createdAt": isoformat(item.created_at),
        "updatedAt": isoformat(item.updated_at),
    }


@router.put("/canned-responses/{item_id}")
async def update_canned(
    item_id: str,
    payload: CannedResponseUpdate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    item = await build_service(session).update_canned(item_id, payload)
    return {
        "id": item.id,
        "title": item.title,
        "content": item.content,
        "category": item.category,
        "shortcut": item.shortcut,
        "isActive": item.is_active,
        "usageCount": item.usage_count,
        "createdAt": isoformat(item.created_at),
        "updatedAt": isoformat(item.updated_at),
    }


@router.delete("/canned-responses/{item_id}")
async def delete_canned(
    item_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    return await build_service(session).delete_canned(item_id)

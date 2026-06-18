from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.compat import isoformat
from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.domain.webhooks.schemas import (
    WebhookCreate,
    WebhookUpdate,
)
from app.domain.webhooks.service import WebhookService
from app.infrastructure.db.repositories.webhooks import WebhookRepository
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter()


def build_service(session: AsyncSession) -> WebhookService:
    return WebhookService(WebhookRepository(session), SQLAlchemyUnitOfWork(session))


@router.get("")
async def list_webhooks(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    response = await build_service(session).list_webhooks(page, limit)
    return [
        {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "url": item.url,
            "method": item.method,
            "headers": item.headers,
            "isActive": item.is_active,
            "triggerOn": item.trigger_on,
            "createdAt": isoformat(item.created_at),
            "updatedAt": isoformat(item.updated_at),
        }
        for item in response.data
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_webhook(
    payload: WebhookCreate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    item = await build_service(session).create_webhook(payload)
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "url": item.url,
        "method": item.method,
        "headers": item.headers,
        "isActive": item.is_active,
        "triggerOn": item.trigger_on,
        "createdAt": isoformat(item.created_at),
        "updatedAt": isoformat(item.updated_at),
    }


@router.get("/{webhook_id}")
async def get_webhook(
    webhook_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    item = await build_service(session).get_webhook(webhook_id)
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "url": item.url,
        "method": item.method,
        "headers": item.headers,
        "isActive": item.is_active,
        "triggerOn": item.trigger_on,
        "createdAt": isoformat(item.created_at),
        "updatedAt": isoformat(item.updated_at),
    }


@router.put("/{webhook_id}")
async def update_webhook(
    webhook_id: str,
    payload: WebhookUpdate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    item = await build_service(session).update_webhook(webhook_id, payload)
    return {
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "url": item.url,
        "method": item.method,
        "headers": item.headers,
        "isActive": item.is_active,
        "triggerOn": item.trigger_on,
        "createdAt": isoformat(item.created_at),
        "updatedAt": isoformat(item.updated_at),
    }


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    return await build_service(session).delete_webhook(webhook_id)


@router.get("/{webhook_id}/deliveries")
async def list_deliveries(
    webhook_id: str,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status_value: str | None = Query(default=None, alias="status"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    response = await build_service(session).list_deliveries(webhook_id, page, limit, status_value)
    return {
        "data": [
            {
                "id": item.id,
                "webhookId": item.webhook_id,
                "event": item.event,
                "payload": item.payload,
                "status": item.status,
                "statusCode": item.status_code,
                "attempts": item.attempts,
                "lastError": item.last_error,
                "nextRetryAt": isoformat(item.next_retry_at),
                "createdAt": isoformat(item.created_at),
                "updatedAt": isoformat(item.updated_at),
            }
            for item in response.data
        ],
        "pagination": {
            "page": response.pagination.page,
            "limit": response.pagination.limit,
            "total": response.pagination.total,
            "totalPages": response.pagination.total_pages,
        },
    }


@router.post("/{webhook_id}/deliveries")
async def retry_delivery_compat(
    webhook_id: str,
    payload: dict,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    delivery_id = payload.get("deliveryId")
    if not delivery_id:
        return {"error": "deliveryId is required"}
    return await build_service(session).retry_delivery(webhook_id, str(delivery_id))


@router.post("/{webhook_id}/deliveries/{delivery_id}/retry")
async def retry_delivery(
    webhook_id: str,
    delivery_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    return await build_service(session).retry_delivery(webhook_id, delivery_id)


@router.post("/test")
async def test_webhook(
    payload: dict,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    webhook_id = payload.get("webhookId")
    if webhook_id:
        return await build_service(session).test_webhook(webhook_id)
    return {"success": False, "error": "webhookId is required"}

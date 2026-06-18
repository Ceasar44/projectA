import httpx
from fastapi import HTTPException, status

from app.core.pagination import build_pagination
from app.domain.webhooks.schemas import (
    WebhookCreate,
    WebhookDeliveryListResponse,
    WebhookListResponse,
    WebhookRead,
    WebhookUpdate,
)


class WebhookService:
    def __init__(self, repo, uow):
        self.repo = repo
        self.uow = uow

    async def list_webhooks(self, page: int, limit: int):
        items, total = await self.repo.list(page, limit)
        return WebhookListResponse(data=items, pagination=build_pagination(page, limit, total))

    async def create_webhook(self, payload: WebhookCreate) -> WebhookRead:
        item = await self.repo.create(payload)
        await self.uow.commit()
        return WebhookRead.model_validate(item)

    async def get_webhook(self, webhook_id: str) -> WebhookRead:
        item = await self.repo.get(webhook_id)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
        return WebhookRead.model_validate(item)

    async def update_webhook(self, webhook_id: str, payload: WebhookUpdate) -> WebhookRead:
        item = await self.repo.update(webhook_id, payload)
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
        await self.uow.commit()
        return WebhookRead.model_validate(item)

    async def delete_webhook(self, webhook_id: str) -> dict[str, bool]:
        deleted = await self.repo.delete(webhook_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
        await self.uow.commit()
        return {"success": True}

    async def list_deliveries(self, webhook_id: str, page: int, limit: int, status_value: str | None):
        items, total = await self.repo.list_deliveries(webhook_id, page, limit, status_value)
        return WebhookDeliveryListResponse(data=items, pagination=build_pagination(page, limit, total))

    async def retry_delivery(self, webhook_id: str, delivery_id: str) -> dict[str, object]:
        ok = await self.repo.retry_delivery(webhook_id, delivery_id)
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")
        await self.uow.commit()
        return {"success": True, "deliveryId": delivery_id}

    async def test_webhook(self, webhook_id: str) -> dict[str, object]:
        webhook = await self.repo.get(webhook_id)
        if not webhook:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

        payload = {
            "event": webhook.trigger_on,
            "test": True,
            "timestamp": "2026-04-15T00:00:00Z",
            "data": {
                "id": "test_123",
                "message": "This is a test payload from Owly",
                "webhookName": webhook.name,
                "triggerEvent": webhook.trigger_on,
            },
        }
        delivery = await self.repo.create_delivery(webhook.id, webhook.trigger_on, payload)
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Owly-Webhook/1.0",
            **{str(key): str(value) for key, value in webhook.headers.items()},
        }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.request(
                    webhook.method,
                    webhook.url,
                    json=payload if webhook.method != "GET" else None,
                    headers=headers,
                )
            body_preview = response.text[:1000]
            await self.repo.update_delivery_result(
                delivery.id,
                status_value="success" if response.is_success else "failed",
                status_code=response.status_code,
                last_error=None if response.is_success else body_preview,
                attempts=1,
            )
            await self.uow.commit()
            return {
                "success": response.is_success,
                "status": response.status_code,
                "statusText": response.reason_phrase,
                "bodyPreview": body_preview,
                "sentPayload": payload,
            }
        except httpx.HTTPError as exc:
            await self.repo.update_delivery_result(
                delivery.id,
                status_value="failed",
                status_code=None,
                last_error=str(exc),
                attempts=1,
            )
            await self.uow.commit()
            return {"success": False, "error": str(exc)}

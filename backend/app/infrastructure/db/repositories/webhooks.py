from datetime import UTC, datetime

from sqlalchemy import func, select

from app.domain.webhooks.schemas import (
    WebhookCreate,
    WebhookDeliveryRead,
    WebhookRead,
    WebhookUpdate,
)
from app.infrastructure.db.models.operations import Webhook, WebhookDelivery


class WebhookRepository:
    def __init__(self, session):
        self.session = session

    async def list(self, page: int, limit: int):
        stmt = select(Webhook).order_by(Webhook.created_at.desc()).offset((page - 1) * limit).limit(limit)
        total = await self.session.scalar(select(func.count()).select_from(Webhook)) or 0
        rows = (await self.session.scalars(stmt)).all()
        return [WebhookRead.model_validate(row) for row in rows], total

    async def create(self, payload: WebhookCreate) -> Webhook:
        item = Webhook(**payload.model_dump(by_alias=False))
        self.session.add(item)
        await self.session.flush()
        return item

    async def get(self, webhook_id: str) -> Webhook | None:
        return await self.session.get(Webhook, webhook_id)

    async def update(self, webhook_id: str, payload: WebhookUpdate) -> Webhook | None:
        item = await self.get(webhook_id)
        if not item:
            return None
        for field, value in payload.model_dump(exclude_none=True, by_alias=False).items():
            setattr(item, field, value)
        await self.session.flush()
        return item

    async def delete(self, webhook_id: str) -> bool:
        item = await self.get(webhook_id)
        if not item:
            return False
        await self.session.delete(item)
        return True

    async def list_deliveries(self, webhook_id: str, page: int, limit: int, status_value: str | None):
        filters = [WebhookDelivery.webhook_id == webhook_id]
        if status_value:
            filters.append(WebhookDelivery.status == status_value)
        stmt = select(WebhookDelivery).where(*filters).order_by(WebhookDelivery.created_at.desc()).offset((page - 1) * limit).limit(limit)
        total = await self.session.scalar(select(func.count()).select_from(WebhookDelivery).where(*filters)) or 0
        rows = (await self.session.scalars(stmt)).all()
        return [WebhookDeliveryRead.model_validate(row) for row in rows], total

    async def retry_delivery(self, webhook_id: str, delivery_id: str) -> bool:
        item = await self.session.scalar(
            select(WebhookDelivery).where(WebhookDelivery.id == delivery_id, WebhookDelivery.webhook_id == webhook_id)
        )
        if not item:
            return False
        item.status = "pending"
        item.attempts += 1
        item.last_error = None
        item.next_retry_at = datetime.now(UTC)
        await self.session.flush()
        return True

    async def create_delivery(self, webhook_id: str, event: str, payload: dict) -> WebhookDelivery:
        item = WebhookDelivery(
            webhook_id=webhook_id,
            event=event,
            payload=payload,
            status="pending",
            attempts=0,
        )
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def update_delivery_result(
        self,
        delivery_id: str,
        *,
        status_value: str,
        status_code: int | None,
        last_error: str | None,
        attempts: int,
    ) -> WebhookDelivery | None:
        item = await self.session.get(WebhookDelivery, delivery_id)
        if not item:
            return None
        item.status = status_value
        item.status_code = status_code
        item.last_error = last_error
        item.attempts = attempts
        item.next_retry_at = None
        await self.session.flush()
        await self.session.refresh(item)
        return item

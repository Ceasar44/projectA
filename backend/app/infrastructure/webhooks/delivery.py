import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.db.models.operations import Webhook, WebhookDelivery

logger = get_logger(__name__)

MAX_ATTEMPTS = 3
RETRY_DELAYS = [5, 30, 300]
DELIVERY_TIMEOUT = 10.0


def generate_signature(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


class WebhookDeliveryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings = get_settings()

    async def deliver_webhook(
        self,
        webhook: Webhook,
        event: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        payload_dict = {
            "event": event,
            "timestamp": datetime.now(UTC).isoformat(),
            "webhookId": webhook.id,
            "data": data,
        }
        payload = json.dumps(payload_dict)

        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event=event,
            payload=payload_dict,
            status="pending",
            attempts=0,
        )
        self.session.add(delivery)
        await self.session.commit()
        await self.session.refresh(delivery)

        success = await self._attempt_delivery(webhook, payload, delivery.id, attempt=1)

        return {"deliveryId": delivery.id, "success": success}

    async def _attempt_delivery(
        self,
        webhook: Webhook,
        payload: str,
        delivery_id: str,
        attempt: int = 1,
    ) -> bool:
        webhook_secret = getattr(self.settings, "webhook_secret", "") or ""
        signature = generate_signature(payload, webhook_secret) if webhook_secret else ""

        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "Owly-Webhook/1.0",
            **(webhook.headers or {}),
        }
        if signature:
            headers["X-Owly-Signature"] = signature

        delivery = await self.session.get(WebhookDelivery, delivery_id)
        if not delivery:
            return False

        try:
            async with httpx.AsyncClient(timeout=DELIVERY_TIMEOUT) as client:
                response = await client.request(
                    method=webhook.method,
                    url=webhook.url,
                    headers=headers,
                    content=payload if webhook.method != "GET" else None,
                )

            if response.is_success:
                delivery.status = "delivered"
                delivery.status_code = response.status_code
                delivery.attempts = attempt
                await self.session.commit()
                return True

            error_message = f"HTTP {response.status_code}: {response.text}"

        except httpx.TimeoutException:
            error_message = "Request timed out"
        except Exception as e:
            error_message = str(e)

        if attempt < MAX_ATTEMPTS:
            retry_delay = RETRY_DELAYS[attempt - 1]
            next_retry_at = datetime.now(UTC) + timedelta(seconds=retry_delay)

            delivery.status = "pending"
            delivery.attempts = attempt
            delivery.last_error = error_message
            delivery.next_retry_at = next_retry_at
            await self.session.commit()

            logger.warning(
                f"Webhook delivery failed, retrying in {retry_delay}s",
                extra={"delivery_id": delivery_id, "webhook_id": webhook.id, "attempt": attempt},
            )

            return False

        delivery.status = "failed"
        delivery.attempts = attempt
        delivery.last_error = error_message
        await self.session.commit()

        logger.error(
            "Webhook delivery permanently failed",
            extra={"delivery_id": delivery_id, "webhook_id": webhook.id},
        )

        return False

    async def retry_delivery(self, delivery_id: str) -> bool:
        delivery = await self.session.scalar(
            select(WebhookDelivery)
            .options(selectinload(WebhookDelivery.webhook))
            .where(WebhookDelivery.id == delivery_id)
        )

        if not delivery or not delivery.webhook:
            return False

        payload = json.dumps(delivery.payload)

        delivery.status = "pending"
        delivery.attempts = 0
        delivery.last_error = None
        await self.session.commit()

        return await self._attempt_delivery(
            webhook=delivery.webhook,
            payload=payload,
            delivery_id=delivery_id,
            attempt=1,
        )

    async def process_pending_retries(self) -> int:
        now = datetime.now(UTC)
        pending_deliveries = list(
            (await self.session.scalars(
                select(WebhookDelivery)
                .options(selectinload(WebhookDelivery.webhook))
                .where(
                    WebhookDelivery.status == "pending",
                    WebhookDelivery.next_retry_at <= now,
                )
            )).all()
        )

        processed = 0
        for delivery in pending_deliveries:
            if delivery.webhook:
                payload = json.dumps(delivery.payload)
                await self._attempt_delivery(
                    webhook=delivery.webhook,
                    payload=payload,
                    delivery_id=delivery.id,
                    attempt=delivery.attempts + 1,
                )
                processed += 1

        return processed

    async def test_webhook(self, webhook_id: str) -> dict[str, Any]:
        webhook = await self.session.get(Webhook, webhook_id)
        if not webhook:
            return {"success": False, "error": "Webhook not found"}

        test_data = {
            "test": True,
            "timestamp": datetime.now(UTC).isoformat(),
        }

        result = await self.deliver_webhook(webhook, "test", test_data)
        return result

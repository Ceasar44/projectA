import re
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.infrastructure.db.models.conversations import Conversation, Customer, CustomerNote, Message

logger = get_logger(__name__)

PII_PATTERNS = [
    ("credit_card", re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "[CARD REDACTED]"),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN REDACTED]"),
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[EMAIL REDACTED]"),
    ("phone", re.compile(r"\b\+?\d{1,3}[\s-]?\(?\d{1,4}\)?[\s-]?\d{1,4}[\s-]?\d{1,9}\b"), "[PHONE REDACTED]"),
    ("ip_address", re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "[IP REDACTED]"),
]


def redact_pii(text: str) -> str:
    redacted = text
    for _, pattern, replacement in PII_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def detect_pii(text: str) -> dict[str, Any]:
    types: list[str] = []
    for name, pattern, _ in PII_PATTERNS:
        if pattern.search(text):
            types.append(name)
    return {"found": len(types) > 0, "types": types}


class GDPRService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def export_customer_data(self, customer_id: str) -> dict[str, Any] | None:
        customer = await self.session.scalar(
            select(Customer)
            .options(
                selectinload(Customer.notes),
                selectinload(Customer.conversations).selectinload(Conversation.messages),
            )
            .where(Customer.id == customer_id)
        )

        if not customer:
            return None

        return {
            "exportDate": datetime.now(UTC).isoformat(),
            "format": "GDPR Data Export",
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "whatsapp": customer.whatsapp,
                "tags": customer.tags,
                "firstContact": customer.first_contact.isoformat() if customer.first_contact else None,
                "lastContact": customer.last_contact.isoformat() if customer.last_contact else None,
                "createdAt": customer.created_at.isoformat() if customer.created_at else None,
            },
            "notes": [
                {
                    "content": note.content,
                    "author": note.author_name,
                    "date": note.created_at.isoformat() if note.created_at else None,
                }
                for note in customer.notes
            ],
            "conversations": [
                {
                    "id": conv.id,
                    "channel": conv.channel,
                    "status": conv.status,
                    "createdAt": conv.created_at.isoformat() if conv.created_at else None,
                    "messages": [
                        {
                            "role": msg.role,
                            "content": msg.content,
                            "date": msg.created_at.isoformat() if msg.created_at else None,
                        }
                        for msg in conv.messages
                    ],
                }
                for conv in customer.conversations
            ],
        }

    async def delete_customer_data(
        self, customer_id: str, hard_delete: bool = False
    ) -> dict[str, Any]:
        customer = await self.session.scalar(
            select(Customer)
            .options(selectinload(Customer.conversations))
            .where(Customer.id == customer_id)
        )

        if not customer:
            return {"success": False, "deletedRecords": 0}

        deleted_records = 0

        if hard_delete:
            for conv in customer.conversations:
                await self.session.execute(
                    select(Message).where(Message.conversation_id == conv.id)
                )
                messages = list(
                    (await self.session.scalars(
                        select(Message).where(Message.conversation_id == conv.id)
                    )).all()
                )
                for msg in messages:
                    await self.session.delete(msg)
                    deleted_records += 1

            for conv in customer.conversations:
                await self.session.delete(conv)
                deleted_records += 1

            notes = list(
                (await self.session.scalars(
                    select(CustomerNote).where(CustomerNote.customer_id == customer_id)
                )).all()
            )
            for note in notes:
                await self.session.delete(note)
                deleted_records += 1

            await self.session.delete(customer)
            deleted_records += 1

        else:
            for conv in customer.conversations:
                messages = list(
                    (await self.session.scalars(
                        select(Message).where(Message.conversation_id == conv.id)
                    )).all()
                )
                for msg in messages:
                    msg.content = "[REDACTED - GDPR]"
                    deleted_records += 1

            for conv in customer.conversations:
                conv.customer_name = "Deleted User"
                conv.customer_contact = ""
                conv.customer_id = None
                deleted_records += 1

            notes = list(
                (await self.session.scalars(
                    select(CustomerNote).where(CustomerNote.customer_id == customer_id)
                )).all()
            )
            for note in notes:
                await self.session.delete(note)
                deleted_records += 1

            await self.session.delete(customer)
            deleted_records += 1

        await self.session.commit()

        logger.info(
            "GDPR data deletion completed",
            extra={"customer_id": customer_id, "hard_delete": hard_delete, "deleted_records": deleted_records},
        )

        return {"success": True, "deletedRecords": deleted_records}

    async def apply_retention_policy(
        self, retention_days: int
    ) -> dict[str, int]:
        cutoff = datetime.now(UTC) - timedelta(days=retention_days)

        old_conversations = list(
            (await self.session.scalars(
                select(Conversation).where(
                    Conversation.status.in_(["resolved", "closed"]),
                    Conversation.updated_at <= cutoff,
                )
            )).all()
        )

        messages_deleted = 0
        for conv in old_conversations:
            messages = list(
                (await self.session.scalars(
                    select(Message).where(Message.conversation_id == conv.id)
                )).all()
            )
            for msg in messages:
                await self.session.delete(msg)
                messages_deleted += 1

        conversations_deleted = len(old_conversations)
        for conv in old_conversations:
            await self.session.delete(conv)

        await self.session.commit()

        logger.info(
            "Retention policy applied",
            extra={
                "retention_days": retention_days,
                "conversations_deleted": conversations_deleted,
                "messages_deleted": messages_deleted,
            },
        )

        return {"conversationsDeleted": conversations_deleted, "messagesDeleted": messages_deleted}

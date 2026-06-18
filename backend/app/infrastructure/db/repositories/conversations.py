from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.domain.conversation.schemas import ConversationCreate, ConversationDetail, ConversationSummary, ConversationUpdate, MessageCreate, MessageRead
from app.infrastructure.db.models.conversations import Conversation, Message


class ConversationRepository:
    def __init__(self, session):
        self.session = session

    async def list(self, page: int, limit: int, channel: str | None, status_value: str | None, search: str | None):
        filters = []
        if channel:
            filters.append(Conversation.channel == channel)
        if status_value:
            filters.append(Conversation.status == status_value)
        if search:
            like = f"%{search}%"
            filters.append(
                or_(
                    Conversation.customer_name.ilike(like),
                    Conversation.customer_contact.ilike(like),
                    Conversation.summary.ilike(like),
                )
            )
        stmt = select(Conversation).where(*filters).order_by(Conversation.updated_at.desc()).offset((page - 1) * limit).limit(limit)
        total_stmt = select(func.count()).select_from(Conversation).where(*filters)
        rows = (await self.session.scalars(stmt)).all()
        total = await self.session.scalar(total_stmt) or 0
        return [ConversationSummary.model_validate(row) for row in rows], total

    async def create(self, payload: ConversationCreate, customer_id: str | None):
        model = Conversation(
            channel=payload.channel,
            customer_name=payload.customer_name or "Unknown",
            customer_contact=payload.customer_contact or "",
            customer_id=customer_id,
            status=payload.status.value,
        )
        self.session.add(model)
        await self.session.flush()
        return model

    async def get_detail(self, conversation_id: str) -> ConversationDetail | None:
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        conversation = await self.session.scalar(stmt)
        if not conversation:
            return None
        return ConversationDetail.model_validate(
            {
                **ConversationSummary.model_validate(conversation).model_dump(),
                "messages": [MessageRead.model_validate(m) for m in conversation.messages],
            }
        )

    async def update(self, conversation_id: str, payload: ConversationUpdate):
        conversation = await self.session.get(Conversation, conversation_id)
        if not conversation:
            return None
        data = payload.model_dump(exclude_none=True, by_alias=False)
        if "status" in data:
            data["status"] = data["status"].value
        for field, value in data.items():
            setattr(conversation, field, value)
        conversation.updated_at = datetime.now(UTC)
        await self.session.flush()
        return conversation

    async def touch(self, conversation_id: str) -> None:
        conversation = await self.session.get(Conversation, conversation_id)
        if conversation:
            conversation.updated_at = datetime.now(UTC)
            await self.session.flush()

    async def exists(self, conversation_id: str) -> bool:
        return await self.session.get(Conversation, conversation_id) is not None


class MessageRepository:
    def __init__(self, session):
        self.session = session

    async def list_by_conversation(self, conversation_id: str) -> list[MessageRead]:
        stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())
        rows = (await self.session.scalars(stmt)).all()
        return [MessageRead.model_validate(row) for row in rows]

    async def create(self, conversation_id: str, payload: MessageCreate) -> MessageRead:
        model = Message(
            conversation_id=conversation_id,
            role=payload.role,
            content=payload.content,
            media_type=payload.media_type,
            media_url=payload.media_url,
        )
        self.session.add(model)
        await self.session.flush()
        return MessageRead.model_validate(model)

from fastapi import HTTPException, status

from app.core.pagination import build_pagination
from app.domain.conversation.schemas import (
    ConversationCreate,
    ConversationDetail,
    ConversationListResponse,
    ConversationUpdate,
    MessageCreate,
    MessageRead,
)


class ConversationService:
    def __init__(self, conversation_repo, message_repo, customer_repo, uow):
        self.conversation_repo = conversation_repo
        self.message_repo = message_repo
        self.customer_repo = customer_repo
        self.uow = uow

    async def list_conversations(self, page: int, limit: int, channel: str | None, status_value: str | None, search: str | None):
        items, total = await self.conversation_repo.list(page, limit, channel, status_value, search)
        return ConversationListResponse(data=items, pagination=build_pagination(page, limit, total))

    async def create_conversation(self, payload: ConversationCreate) -> ConversationDetail:
        customer_id = None
        if payload.customer_contact:
            customer_id = await self.customer_repo.resolve_customer(
                payload.channel,
                payload.customer_contact,
                payload.customer_name or "Unknown",
            )
        conversation = await self.conversation_repo.create(payload, customer_id)
        await self.uow.commit()
        return await self.get_conversation(conversation.id)

    async def get_conversation(self, conversation_id: str) -> ConversationDetail:
        conversation = await self.conversation_repo.get_detail(conversation_id)
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        return conversation

    async def update_conversation(self, conversation_id: str, payload: ConversationUpdate) -> ConversationDetail:
        updated = await self.conversation_repo.update(conversation_id, payload)
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        await self.uow.commit()
        return await self.get_conversation(conversation_id)

    async def list_messages(self, conversation_id: str) -> list[MessageRead]:
        await self._ensure_exists(conversation_id)
        return await self.message_repo.list_by_conversation(conversation_id)

    async def create_message(self, conversation_id: str, payload: MessageCreate) -> MessageRead:
        await self._ensure_exists(conversation_id)
        message = await self.message_repo.create(conversation_id, payload)
        await self.conversation_repo.touch(conversation_id)
        await self.uow.commit()
        return message

    async def _ensure_exists(self, conversation_id: str) -> None:
        exists = await self.conversation_repo.exists(conversation_id)
        if not exists:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

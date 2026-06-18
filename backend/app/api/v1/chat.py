from fastapi import APIRouter, Depends
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.domain.conversation.schemas import ConversationCreate, MessageCreate
from app.domain.customer_support.service import (
    CustomerSupportAgentService,
    build_conversation_service,
)
from app.infrastructure.realtime import event_bus

router = APIRouter()


class ChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str = Field(min_length=1)
    conversation_id: str | None = Field(default=None, alias="conversationId")
    channel: str = "api"
    customer_name: str | None = Field(default=None, alias="customerName")
    customer_contact: str | None = Field(default=None, alias="customerContact")


@router.post("")
async def chat(payload: ChatRequest, session: AsyncSession = Depends(get_session)) -> dict[str, object]:
    message = payload.message.strip()
    if not message:
        return ORJSONResponse({"error": "Message is required"}, status_code=400)
    if len(message) > 10000:
        return ORJSONResponse({"error": "Message exceeds maximum length of 10000 characters"}, status_code=400)

    conversation_service = build_conversation_service(session)
    conversation_id = payload.conversation_id
    if not conversation_id:
        conversation = await conversation_service.create_conversation(
            ConversationCreate(
                channel=payload.channel,
                customerName=payload.customer_name or "API User",
                customerContact=payload.customer_contact,
            )
        )
        conversation_id = conversation.id

    user_message = await conversation_service.create_message(
        conversation_id,
        MessageCreate(role="customer", content=message),
    )
    event_bus.emit_new_message(
        conversation_id,
        {
            "id": user_message.id,
            "conversationId": conversation_id,
            "role": user_message.role,
            "content": user_message.content,
        },
    )

    result = await CustomerSupportAgentService(session).reply_to_conversation(
        conversation_id,
        message,
        source="chat_api",
        write_auto_reply_log=False,
    )

    if result.assistant_message:
        event_bus.emit_new_message(conversation_id, result.assistant_message)
    event_bus.emit_conversation_update(
        conversation_id,
        {
            "status": result.status,
            "sentiment": result.sentiment,
            "intent": result.intent,
            "confidence": result.confidence,
            "escalationReason": result.escalation_reason,
        },
    )

    return result.to_api_response()

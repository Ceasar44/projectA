from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.infrastructure.db.models.conversations import Conversation, Message
from app.infrastructure.db.models.team import Ticket

router = APIRouter()


@router.get("")
async def get_stats(
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict:
    total_conversations = await session.scalar(select(func.count()).select_from(Conversation)) or 0

    active_conversations = await session.scalar(
        select(func.count()).select_from(Conversation).where(Conversation.status == "active")
    ) or 0

    resolved_conversations = await session.scalar(
        select(func.count()).select_from(Conversation).where(Conversation.status == "resolved")
    ) or 0

    total_messages = await session.scalar(select(func.count()).select_from(Message)) or 0

    total_tickets = await session.scalar(select(func.count()).select_from(Ticket)) or 0

    open_tickets = await session.scalar(
        select(func.count()).select_from(Ticket).where(Ticket.status == "open")
    ) or 0

    by_channel = list(
        (
            await session.execute(
                select(Conversation.channel, func.count(Conversation.id).label("count"))
                .group_by(Conversation.channel)
            )
        ).all()
    )

    resolution_rate = round((resolved_conversations / total_conversations) * 100) if total_conversations else 0
    channels: dict[str, int] = {}
    for channel, count in by_channel:
        channels[str(channel)] = int(count)

    return {
        "totalConversations": total_conversations,
        "activeConversations": active_conversations,
        "resolvedConversations": resolved_conversations,
        "totalTickets": total_tickets,
        "openTickets": open_tickets,
        "totalMessages": total_messages,
        "resolutionRate": resolution_rate,
        "channels": channels,
    }

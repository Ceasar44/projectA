from sqlalchemy import desc, func, select

from app.infrastructure.db.models.conversations import Conversation, Message
from app.infrastructure.db.models.operations import ActivityLog
from app.infrastructure.db.models.team import Ticket


class AnalyticsRepository:
    def __init__(self, session):
        self.session = session

    async def stats(self) -> dict[str, object]:
        total_conversations = await self.session.scalar(select(func.count()).select_from(Conversation)) or 0
        active_conversations = await self.session.scalar(select(func.count()).select_from(Conversation).where(Conversation.status == "active")) or 0
        total_tickets = await self.session.scalar(select(func.count()).select_from(Ticket)) or 0
        total_messages = await self.session.scalar(select(func.count()).select_from(Message)) or 0
        return {
            "totalConversations": total_conversations,
            "activeConversations": active_conversations,
            "totalTickets": total_tickets,
            "totalMessages": total_messages,
        }

    async def overview(self) -> dict[str, object]:
        rows = (
            await self.session.execute(
                select(Conversation.channel, func.count(Conversation.id)).group_by(Conversation.channel)
            )
        ).all()
        tickets = (
            await self.session.execute(
                select(Ticket.status, func.count(Ticket.id)).group_by(Ticket.status)
            )
        ).all()
        return {
            "channelBreakdown": [{"channel": channel, "count": count} for channel, count in rows],
            "ticketsByStatus": [{"status": status, "count": count} for status, count in tickets],
        }

    async def activity(self, page: int, limit: int):
        stmt = select(ActivityLog).order_by(desc(ActivityLog.created_at)).offset((page - 1) * limit).limit(limit)
        total = await self.session.scalar(select(func.count()).select_from(ActivityLog)) or 0
        rows = (await self.session.scalars(stmt)).all()
        return rows, total

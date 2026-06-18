from sqlalchemy import func, select

from app.infrastructure.db.models.conversations import Conversation, Message
from app.infrastructure.db.models.team import Ticket


class AnalyticsQueryService:
    def __init__(self, session):
        self.session = session

    async def stats(self) -> dict[str, int]:
        total_conversations = await self.session.scalar(select(func.count()).select_from(Conversation)) or 0
        total_messages = await self.session.scalar(select(func.count()).select_from(Message)) or 0
        total_tickets = await self.session.scalar(select(func.count()).select_from(Ticket)) or 0
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "total_tickets": total_tickets,
        }

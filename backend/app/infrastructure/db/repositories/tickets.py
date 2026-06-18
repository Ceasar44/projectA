from sqlalchemy import func, select

from app.domain.ticket.schemas import TicketCreate, TicketDetail, TicketUpdate
from app.infrastructure.db.models.team import Ticket


class TicketRepository:
    def __init__(self, session):
        self.session = session

    async def list(self, page: int, limit: int, status_value: str | None, priority: str | None):
        filters = []
        if status_value:
            filters.append(Ticket.status == status_value)
        if priority:
            filters.append(Ticket.priority == priority)
        stmt = select(Ticket).where(*filters).order_by(Ticket.created_at.desc()).offset((page - 1) * limit).limit(limit)
        total_stmt = select(func.count()).select_from(Ticket).where(*filters)
        rows = (await self.session.scalars(stmt)).all()
        total = await self.session.scalar(total_stmt) or 0
        return [TicketDetail.model_validate(row) for row in rows], total

    async def create(self, payload: TicketCreate) -> Ticket:
        data = payload.model_dump(by_alias=False)
        for enum_field in ("priority", "status"):
            data[enum_field] = data[enum_field].value
        ticket = Ticket(**data)
        self.session.add(ticket)
        await self.session.flush()
        return ticket

    async def get(self, ticket_id: str) -> Ticket | None:
        return await self.session.get(Ticket, ticket_id)

    async def update(self, ticket_id: str, payload: TicketUpdate) -> Ticket | None:
        ticket = await self.get(ticket_id)
        if not ticket:
            return None
        data = payload.model_dump(exclude_none=True, by_alias=False)
        for enum_field in ("priority", "status"):
            if enum_field in data:
                data[enum_field] = data[enum_field].value
        for field, value in data.items():
            setattr(ticket, field, value)
        await self.session.flush()
        return ticket

    async def delete(self, ticket_id: str) -> bool:
        ticket = await self.get(ticket_id)
        if not ticket:
            return False
        await self.session.delete(ticket)
        return True

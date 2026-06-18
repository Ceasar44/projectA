from fastapi import HTTPException, status

from app.core.pagination import build_pagination
from app.domain.ticket.schemas import TicketCreate, TicketDetail, TicketListResponse, TicketUpdate


class TicketService:
    def __init__(self, ticket_repo, uow):
        self.ticket_repo = ticket_repo
        self.uow = uow

    @staticmethod
    def _to_detail(ticket) -> TicketDetail:
        return TicketDetail(
            id=ticket.id,
            title=ticket.title,
            description=ticket.description,
            status=ticket.status,
            priority=ticket.priority,
            resolution=ticket.resolution,
            conversationId=ticket.conversation_id,
            departmentId=ticket.department_id,
            assignedToId=ticket.assigned_to_id,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
        )

    async def list_tickets(self, page: int, limit: int, status_value: str | None, priority: str | None):
        items, total = await self.ticket_repo.list(page, limit, status_value, priority)
        return TicketListResponse(data=items, pagination=build_pagination(page, limit, total))

    async def create_ticket(self, payload: TicketCreate) -> TicketDetail:
        ticket = await self.ticket_repo.create(payload)
        await self.uow.commit()
        await self.uow.session.refresh(ticket)
        return self._to_detail(ticket)

    async def get_ticket(self, ticket_id: str) -> TicketDetail:
        ticket = await self.ticket_repo.get(ticket_id)
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        return self._to_detail(ticket)

    async def update_ticket(self, ticket_id: str, payload: TicketUpdate) -> TicketDetail:
        ticket = await self.ticket_repo.update(ticket_id, payload)
        if not ticket:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        await self.uow.commit()
        await self.uow.session.refresh(ticket)
        return self._to_detail(ticket)

    async def delete_ticket(self, ticket_id: str) -> dict[str, bool]:
        if not await self.ticket_repo.delete(ticket_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
        await self.uow.commit()
        return {"success": True}

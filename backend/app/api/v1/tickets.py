from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.compat import isoformat
from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.domain.ticket.schemas import TicketCreate, TicketUpdate
from app.domain.ticket.service import TicketService
from app.infrastructure.db.models.conversations import Conversation
from app.infrastructure.db.models.team import Department, TeamMember, Ticket
from app.infrastructure.db.repositories.tickets import TicketRepository
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter()


def build_service(session: AsyncSession) -> TicketService:
    return TicketService(TicketRepository(session), SQLAlchemyUnitOfWork(session))


def serialize_ticket(ticket: Ticket, conversation: Conversation | None, department: Department | None, assigned_to: TeamMember | None) -> dict[str, object]:
    return {
        "id": ticket.id,
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "resolution": ticket.resolution,
        "conversationId": ticket.conversation_id,
        "departmentId": ticket.department_id,
        "assignedToId": ticket.assigned_to_id,
        "conversation": (
            {
                "id": conversation.id,
                "customerName": conversation.customer_name,
                "channel": conversation.channel,
                "status": conversation.status,
            }
            if conversation
            else None
        ),
        "department": {"id": department.id, "name": department.name} if department else None,
        "assignedTo": (
            {"id": assigned_to.id, "name": assigned_to.name, "email": assigned_to.email}
            if assigned_to
            else None
        ),
        "createdAt": isoformat(ticket.created_at),
        "updatedAt": isoformat(ticket.updated_at),
    }


@router.get("")
async def list_tickets(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    status_value: str | None = Query(default=None, alias="status"),
    priority: str | None = None,
    department_id: str | None = Query(default=None, alias="departmentId"),
    search: str | None = None,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    stmt = select(Ticket).order_by(Ticket.created_at.desc())
    if status_value:
        stmt = stmt.where(Ticket.status == status_value)
    if priority:
        stmt = stmt.where(Ticket.priority == priority)
    if department_id:
        stmt = stmt.where(Ticket.department_id == department_id)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(Ticket.title.ilike(like), Ticket.description.ilike(like)))
    count_stmt = select(func.count()).select_from(Ticket)
    if status_value:
        count_stmt = count_stmt.where(Ticket.status == status_value)
    if priority:
        count_stmt = count_stmt.where(Ticket.priority == priority)
    if department_id:
        count_stmt = count_stmt.where(Ticket.department_id == department_id)
    if search:
        like = f"%{search}%"
        count_stmt = count_stmt.where(or_(Ticket.title.ilike(like), Ticket.description.ilike(like)))
    tickets = list((await session.scalars(stmt.offset((page - 1) * limit).limit(limit))).all())
    total = await session.scalar(count_stmt) or 0
    conversation_ids = [item.conversation_id for item in tickets if item.conversation_id]
    department_ids = [item.department_id for item in tickets if item.department_id]
    member_ids = [item.assigned_to_id for item in tickets if item.assigned_to_id]
    conversations = {row.id: row for row in (await session.scalars(select(Conversation).where(Conversation.id.in_(conversation_ids)))).all()} if conversation_ids else {}
    departments = {row.id: row for row in (await session.scalars(select(Department).where(Department.id.in_(department_ids)))).all()} if department_ids else {}
    members = {row.id: row for row in (await session.scalars(select(TeamMember).where(TeamMember.id.in_(member_ids)))).all()} if member_ids else {}
    return {
        "data": [
            serialize_ticket(
                ticket,
                conversations.get(ticket.conversation_id),
                departments.get(ticket.department_id),
                members.get(ticket.assigned_to_id),
            )
            for ticket in tickets
        ],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": max(1, (total + limit - 1) // limit),
        },
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: dict[str, object],
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    title = str(payload.get("title", "")).strip()
    if not title:
        return ORJSONResponse({"error": "Ticket title is required"}, status_code=400)
    item = await build_service(session).create_ticket(TicketCreate.model_validate(payload))
    ticket = await session.get(Ticket, item.id)
    conversation = await session.get(Conversation, ticket.conversation_id) if ticket.conversation_id else None
    department = await session.get(Department, ticket.department_id) if ticket.department_id else None
    assigned_to = await session.get(TeamMember, ticket.assigned_to_id) if ticket.assigned_to_id else None
    return serialize_ticket(ticket, conversation, department, assigned_to)


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    await build_service(session).get_ticket(ticket_id)
    ticket = await session.get(Ticket, ticket_id)
    conversation = await session.get(Conversation, ticket.conversation_id) if ticket.conversation_id else None
    department = await session.get(Department, ticket.department_id) if ticket.department_id else None
    assigned_to = await session.get(TeamMember, ticket.assigned_to_id) if ticket.assigned_to_id else None
    return serialize_ticket(ticket, conversation, department, assigned_to)


@router.put("/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    payload: TicketUpdate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    await build_service(session).update_ticket(ticket_id, payload)
    ticket = await session.get(Ticket, ticket_id)
    conversation = await session.get(Conversation, ticket.conversation_id) if ticket.conversation_id else None
    department = await session.get(Department, ticket.department_id) if ticket.department_id else None
    assigned_to = await session.get(TeamMember, ticket.assigned_to_id) if ticket.assigned_to_id else None
    return serialize_ticket(ticket, conversation, department, assigned_to)


@router.delete("/{ticket_id}")
async def delete_ticket(
    ticket_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    return await build_service(session).delete_ticket(ticket_id)

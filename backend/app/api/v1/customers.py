from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.compat import isoformat
from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.domain.customer.schemas import CustomerCreate, CustomerDetail, CustomerUpdate
from app.domain.customer.service import CustomerService
from app.domain.gdpr import GDPRService
from app.infrastructure.db.models.conversations import Conversation, Customer, CustomerNote, Message
from app.infrastructure.db.repositories.conversations import ConversationRepository
from app.infrastructure.db.repositories.customers import CustomerNoteRepository, CustomerRepository
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork

router = APIRouter()


def build_service(session: AsyncSession) -> CustomerService:
    return CustomerService(
        customer_repo=CustomerRepository(session),
        note_repo=CustomerNoteRepository(session),
        conversation_repo=ConversationRepository(session),
        uow=SQLAlchemyUnitOfWork(session),
    )


def serialize_conversation_summary(conversation: Conversation) -> dict[str, object]:
    messages = sorted(conversation.messages, key=lambda item: item.created_at or "", reverse=True)
    return {
        "id": conversation.id,
        "channel": conversation.channel,
        "customerName": conversation.customer_name,
        "customerContact": conversation.customer_contact,
        "status": conversation.status,
        "createdAt": isoformat(conversation.created_at),
        "updatedAt": isoformat(conversation.updated_at),
        "_count": {"messages": len(conversation.messages)},
        "messages": [
            {
                "id": msg.id,
                "conversationId": msg.conversation_id,
                "role": msg.role,
                "content": msg.content,
                "mediaType": msg.media_type,
                "mediaUrl": msg.media_url,
                "createdAt": isoformat(msg.created_at),
            }
            for msg in messages[:1]
        ],
    }


def serialize_note(note: CustomerNote) -> dict[str, object]:
    return {
        "id": note.id,
        "customerId": note.customer_id,
        "content": note.content,
        "authorName": note.author_name,
        "createdAt": isoformat(note.created_at),
    }


def serialize_customer_detail(customer: Customer) -> dict[str, object]:
    conversations = sorted(customer.conversations, key=lambda item: item.updated_at or "", reverse=True)
    notes = sorted(customer.notes, key=lambda item: item.created_at or "", reverse=True)
    return {
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "phone": customer.phone,
        "whatsapp": customer.whatsapp,
        "tags": customer.tags,
        "isBlocked": customer.is_blocked,
        "notes": [serialize_note(note) for note in notes],
        "metadata": customer.metadata_json or {},
        "firstContact": isoformat(customer.first_contact),
        "lastContact": isoformat(customer.last_contact),
        "conversations": [serialize_conversation_summary(conv) for conv in conversations],
        "_count": {"notes": len(notes)},
        "createdAt": isoformat(customer.created_at),
        "updatedAt": isoformat(customer.updated_at),
    }


@router.get("")
async def list_customers(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    is_blocked: bool | None = Query(default=None, alias="isBlocked"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    filters = []
    if search:
        like = f"%{search}%"
        filters.append(
            or_(
                Customer.name.ilike(like),
                Customer.email.ilike(like),
                Customer.phone.ilike(like),
                Customer.whatsapp.ilike(like),
            )
        )
    if is_blocked is not None:
        filters.append(Customer.is_blocked == is_blocked)
    stmt = (
        select(Customer)
        .options(selectinload(Customer.notes))
        .where(*filters)
        .order_by(Customer.last_contact.desc())
        .offset((page - 1) * limit)
        .limit(limit)
    )
    total = await session.scalar(select(func.count()).select_from(Customer).where(*filters)) or 0
    customers = list((await session.scalars(stmt)).all())
    return {
        "data": [
            {
                "id": customer.id,
                "name": customer.name,
                "email": customer.email,
                "phone": customer.phone,
                "whatsapp": customer.whatsapp,
                "tags": customer.tags,
                "isBlocked": customer.is_blocked,
                "firstContact": isoformat(customer.first_contact),
                "lastContact": isoformat(customer.last_contact),
                "_count": {"notes": len(customer.notes)},
                "createdAt": isoformat(customer.created_at),
                "updatedAt": isoformat(customer.updated_at),
            }
            for customer in customers
        ],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": max(1, (total + limit - 1) // limit),
        },
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: dict[str, object],
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    name = str(payload.get("name", "")).strip()
    if not name:
        return ORJSONResponse({"error": "Name is required"}, status_code=400)
    created = await build_service(session).create_customer(CustomerCreate.model_validate(payload))
    customer = await session.scalar(
        select(Customer)
        .options(
            selectinload(Customer.notes),
            selectinload(Customer.conversations).selectinload(Conversation.messages),
        )
        .where(Customer.id == created.id)
    )
    return serialize_customer_detail(customer)


@router.get("/{customer_id}")
async def get_customer(
    customer_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    customer = await session.scalar(
        select(Customer)
        .options(
            selectinload(Customer.notes),
            selectinload(Customer.conversations).selectinload(Conversation.messages),
        )
        .where(Customer.id == customer_id)
    )
    if not customer:
        await build_service(session).get_customer(customer_id)
        customer = await session.scalar(
            select(Customer)
            .options(
                selectinload(Customer.notes),
                selectinload(Customer.conversations).selectinload(Conversation.messages),
            )
            .where(Customer.id == customer_id)
        )
    return serialize_customer_detail(customer)


@router.put("/{customer_id}")
async def update_customer(
    customer_id: str,
    payload: CustomerUpdate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    await build_service(session).update_customer(customer_id, payload)
    customer = await session.scalar(
        select(Customer)
        .options(
            selectinload(Customer.notes),
            selectinload(Customer.conversations).selectinload(Conversation.messages),
        )
        .where(Customer.id == customer_id)
    )
    return serialize_customer_detail(customer)


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    return await build_service(session).delete_customer(customer_id)


@router.get("/{customer_id}/notes")
async def list_customer_notes(
    customer_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    return await build_service(session).list_notes(customer_id)


@router.post("/{customer_id}/notes")
async def create_customer_note(
    customer_id: str,
    payload: dict,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    return await build_service(session).create_note(customer_id, payload.get("content", ""), payload.get("authorName", "Admin"))


@router.get("/{customer_id}/conversations")
async def customer_conversations(
    customer_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    customer = await session.scalar(
        select(Customer)
        .options(selectinload(Customer.conversations).selectinload(Conversation.messages))
        .where(Customer.id == customer_id)
    )
    if not customer:
        await build_service(session).get_customer(customer_id)
    return {
        "customerId": customer_id,
        "customerName": customer.name,
        "data": [serialize_conversation_summary(conv) for conv in sorted(customer.conversations, key=lambda item: item.updated_at or "", reverse=True)],
    }


@router.get("/{customer_id}/gdpr/export")
async def gdpr_export(
    customer_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    gdpr_service = GDPRService(session)
    data = await gdpr_service.export_customer_data(customer_id)
    if not data:
        return {"customerId": customer_id, "error": "Customer not found"}
    return data


@router.delete("/{customer_id}/gdpr/delete")
async def gdpr_delete(
    customer_id: str,
    hard_delete: bool = Query(default=False, alias="hardDelete"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    gdpr_service = GDPRService(session)
    result = await gdpr_service.delete_customer_data(customer_id, hard_delete=hard_delete)
    return {"customerId": customer_id, **result}

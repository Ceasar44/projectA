from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import ORJSONResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.compat import isoformat
from app.api.deps import get_auth_context, get_session
from app.domain.ai_workspace.service import AIWorkspaceService
from app.domain.automation.service import AutomationService
from app.domain.auth.schemas import AuthContext
from app.domain.conversation.engine import ConversationEngine, RoutingStrategy
from app.domain.conversation.schemas import (
    ConversationCreate,
    ConversationUpdate,
    MessageCreate,
)
from app.domain.conversation.service import ConversationService
from app.infrastructure.db.models.conversations import Conversation, ConversationTag, InternalNote, Message
from app.infrastructure.db.models.team import Ticket
from app.infrastructure.db.repositories.automation import AutomationRuleRepository
from app.infrastructure.db.repositories.conversations import ConversationRepository, MessageRepository
from app.infrastructure.db.repositories.customers import CustomerRepository
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.realtime import event_bus

router = APIRouter()


def build_service(session: AsyncSession) -> ConversationService:
    return ConversationService(
        conversation_repo=ConversationRepository(session),
        message_repo=MessageRepository(session),
        customer_repo=CustomerRepository(session),
        uow=SQLAlchemyUnitOfWork(session),
    )


def serialize_message(message) -> dict[str, object]:
    return {
        "id": message.id,
        "conversationId": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "mediaType": message.media_type,
        "mediaUrl": message.media_url,
        "createdAt": isoformat(message.created_at),
    }


def serialize_conversation(conversation: Conversation, include_all_messages: bool) -> dict[str, object]:
    messages = sorted(conversation.messages, key=lambda item: item.created_at or "")
    preview_messages = messages if include_all_messages else list(reversed(messages[-1:]))
    tags = [
        {"id": link.tag.id, "name": link.tag.name, "color": link.tag.color or ""}
        for link in sorted(conversation.tag_links, key=lambda item: item.created_at or "")
        if link.tag
    ]
    return {
        "id": conversation.id,
        "channel": conversation.channel,
        "customerName": conversation.customer_name,
        "customerContact": conversation.customer_contact,
        "status": conversation.status,
        "summary": conversation.summary or "",
        "messages": [serialize_message(message) for message in preview_messages],
        "_count": {"messages": len(messages)},
        "tags": tags,
        "createdAt": isoformat(conversation.created_at),
        "updatedAt": isoformat(conversation.updated_at),
    }


def serialize_conversation_detail(conversation: Conversation) -> dict[str, object]:
    data = serialize_conversation(conversation, include_all_messages=True)
    data["customer"] = (
        {
            "id": conversation.customer.id,
            "name": conversation.customer.name,
            "email": conversation.customer.email,
            "phone": conversation.customer.phone,
            "whatsapp": conversation.customer.whatsapp,
            "tags": conversation.customer.tags,
            "isBlocked": conversation.customer.is_blocked,
        }
        if conversation.customer
        else None
    )
    data["tickets"] = [
        {
            "id": ticket.id,
            "title": ticket.title,
            "description": ticket.description,
            "status": ticket.status,
            "priority": ticket.priority,
            "resolution": ticket.resolution,
            "departmentId": ticket.department_id,
            "assignedToId": ticket.assigned_to_id,
            "department": (
                {"id": ticket.department.id, "name": ticket.department.name}
                if ticket.department
                else None
            ),
            "assignedTo": (
                {
                    "id": ticket.assigned_to.id,
                    "name": ticket.assigned_to.name,
                    "email": ticket.assigned_to.email,
                }
                if ticket.assigned_to
                else None
            ),
            "createdAt": isoformat(ticket.created_at),
            "updatedAt": isoformat(ticket.updated_at),
        }
        for ticket in conversation.tickets
    ]
    return data


def build_automation_service(session: AsyncSession) -> AutomationService:
    return AutomationService(AutomationRuleRepository(session), SQLAlchemyUnitOfWork(session))


@router.get("")
async def list_conversations(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    channel: str | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    search: str | None = None,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
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
    rows = list(
        (
            await session.scalars(
                select(Conversation)
                .options(
                    selectinload(Conversation.messages),
                    selectinload(Conversation.tag_links).selectinload(ConversationTag.tag),
                )
                .where(*filters)
                .order_by(Conversation.updated_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            )
        ).all()
    )
    total = await session.scalar(select(func.count()).select_from(Conversation).where(*filters)) or 0
    return {
        "data": [serialize_conversation(row, include_all_messages=False) for row in rows],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": max(1, (total + limit - 1) // limit),
        },
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: dict[str, object],
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    channel = str(payload.get("channel", "")).strip()
    if not channel:
        return ORJSONResponse({"error": "Channel is required"}, status_code=400)
    created = await build_service(session).create_conversation(ConversationCreate.model_validate(payload))
    row = await session.scalar(
        select(Conversation)
        .options(
            selectinload(Conversation.messages),
            selectinload(Conversation.tag_links).selectinload(ConversationTag.tag),
        )
        .where(Conversation.id == created.id)
    )
    return serialize_conversation(row, include_all_messages=True)


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    row = await session.scalar(
        select(Conversation)
        .options(
            selectinload(Conversation.messages),
            selectinload(Conversation.customer),
            selectinload(Conversation.tag_links).selectinload(ConversationTag.tag),
            selectinload(Conversation.tickets).selectinload(Ticket.department),
            selectinload(Conversation.tickets).selectinload(Ticket.assigned_to),
        )
        .where(Conversation.id == conversation_id)
    )
    if not row:
        await build_service(session).get_conversation(conversation_id)
        row = await session.scalar(
            select(Conversation)
            .options(
                selectinload(Conversation.messages),
                selectinload(Conversation.customer),
                selectinload(Conversation.tag_links).selectinload(ConversationTag.tag),
                selectinload(Conversation.tickets).selectinload(Ticket.department),
                selectinload(Conversation.tickets).selectinload(Ticket.assigned_to),
            )
            .where(Conversation.id == conversation_id)
        )
    return serialize_conversation_detail(row)


@router.put("/{conversation_id}")
async def update_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    await build_service(session).update_conversation(conversation_id, payload)
    row = await session.scalar(
        select(Conversation)
        .options(
            selectinload(Conversation.messages),
            selectinload(Conversation.customer),
            selectinload(Conversation.tag_links).selectinload(ConversationTag.tag),
            selectinload(Conversation.tickets).selectinload(Ticket.department),
            selectinload(Conversation.tickets).selectinload(Ticket.assigned_to),
        )
        .where(Conversation.id == conversation_id)
    )
    return serialize_conversation_detail(row)


@router.get("/{conversation_id}/messages")
async def list_messages(
    conversation_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    return [
        {
            "id": item.id,
            "conversationId": conversation_id,
            "role": item.role,
            "content": item.content,
            "mediaType": item.media_type,
            "mediaUrl": item.media_url,
            "createdAt": isoformat(item.created_at),
        }
        for item in await build_service(session).list_messages(conversation_id)
    ]


@router.post("/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
async def create_message(
    conversation_id: str,
    payload: MessageCreate,
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    item = await build_service(session).create_message(conversation_id, payload)
    message_data = {
        "id": item.id,
        "conversationId": conversation_id,
        "role": item.role,
        "content": item.content,
        "mediaType": item.media_type,
        "mediaUrl": item.media_url,
        "createdAt": isoformat(item.created_at),
    }
    event_bus.emit_new_message(conversation_id, message_data)
    if payload.role == "customer":
        conversation = await session.get(Conversation, conversation_id)
        if conversation:
            matched = await build_automation_service(session).evaluate_rules(
                {
                    "content": payload.content,
                    "channel": conversation.channel,
                    "customerName": conversation.customer_name,
                },
                {
                    "id": conversation.id,
                    "channel": conversation.channel,
                    "customerName": conversation.customer_name,
                },
            )
            if matched:
                engine = ConversationEngine(session)
                for match in matched:
                    await engine.execute_macro(
                        conversation_id,
                        [dict(action) for action in match.get("actions", [])],
                        auth.name,
                    )
            auto_reply_result = await AIWorkspaceService(session).maybe_auto_reply(
                conversation_id,
                payload.content,
            )
            if auto_reply_result and auto_reply_result.get("status") == "sent":
                auto_message = auto_reply_result.get("message") or {}
                event_bus.emit_new_message(conversation_id, auto_message)
    return message_data


@router.post("/{conversation_id}/transfer")
async def transfer_conversation(
    conversation_id: str,
    payload: dict[str, object],
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    to_member_id = payload.get("toMemberId")
    note = payload.get("note")

    if not to_member_id:
        return {"success": False, "error": "toMemberId is required"}

    engine = ConversationEngine(session)
    success = await engine.transfer_conversation(
        conversation_id,
        str(to_member_id),
        auth.name,
        str(note) if note else None,
    )

    if success:
        event_bus.emit_conversation_update(
            conversation_id, {"transferred": True, "toMemberId": to_member_id}
        )

    return {"success": success}


@router.post("/{conversation_id}/merge")
async def merge_conversations(
    conversation_id: str,
    payload: dict[str, str],
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    secondary_id = payload.get("secondaryId")
    if not secondary_id:
        return {"success": False, "error": "secondaryId is required"}

    engine = ConversationEngine(session)
    success = await engine.merge_conversations(conversation_id, secondary_id)
    return {"success": success}


@router.post("/{conversation_id}/snooze")
async def snooze_conversation(
    conversation_id: str,
    payload: dict[str, str],
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    snooze_until_str = payload.get("snoozeUntil")
    reason = payload.get("reason", "")

    if not snooze_until_str:
        return {"success": False, "error": "snoozeUntil is required"}

    try:
        snooze_until = datetime.fromisoformat(snooze_until_str.replace("Z", "+00:00"))
    except ValueError:
        return {"success": False, "error": "Invalid date format"}

    engine = ConversationEngine(session)
    success = await engine.snooze_conversation(
        conversation_id, snooze_until, reason, auth.name
    )

    if success:
        event_bus.emit_conversation_update(
            conversation_id, {"status": "snoozed", "snoozeUntil": snooze_until_str}
        )

    return {"success": success}


@router.post("/{conversation_id}/satisfaction")
async def set_satisfaction(
    conversation_id: str,
    payload: dict[str, int],
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    satisfaction = payload.get("satisfaction")

    if satisfaction is None or not (1 <= satisfaction <= 5):
        return {"success": False, "error": "satisfaction must be between 1 and 5"}

    conversation = await session.get(Conversation, conversation_id)
    if not conversation:
        return {"success": False, "error": "Conversation not found"}

    conversation.satisfaction = satisfaction
    await session.commit()

    return {"success": True}


@router.post("/{conversation_id}/route-to")
async def route_conversation(
    conversation_id: str,
    payload: dict[str, object],
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    strategy_str = payload.get("strategy", "skill_based")
    required_expertise = payload.get("requiredExpertise")
    department_id = payload.get("departmentId")

    try:
        strategy = RoutingStrategy(str(strategy_str))
    except ValueError:
        strategy = RoutingStrategy.SKILL_BASED

    engine = ConversationEngine(session)
    result = await engine.route_conversation(
        conversation_id,
        strategy,
        str(required_expertise) if required_expertise else None,
        str(department_id) if department_id else None,
    )

    if not result:
        return {"success": False, "error": "No available agent found"}

    return {
        "success": True,
        "assignedToId": result.assigned_to_id,
        "assignedToName": result.assigned_to_name,
        "departmentId": result.department_id,
        "departmentName": result.department_name,
        "reason": result.reason,
    }


@router.post("/{conversation_id}/macro")
async def execute_macro(
    conversation_id: str,
    payload: dict[str, object],
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    actions = payload.get("actions", [])
    if not isinstance(actions, list):
        return {"executed": 0, "errors": ["actions must be a list"]}

    engine = ConversationEngine(session)
    executed, errors = await engine.execute_macro(
        conversation_id,
        [dict(a) for a in actions],
        auth.name,
    )

    return {"executed": executed, "errors": errors}


@router.get("/{conversation_id}/notes")
async def list_notes(
    conversation_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, object]]:
    notes = list(
        (
            await session.scalars(
                select(InternalNote)
                .where(InternalNote.conversation_id == conversation_id)
                .order_by(InternalNote.created_at.desc())
            )
        ).all()
    )
    return [
        {
            "id": note.id,
            "conversationId": conversation_id,
            "content": note.content,
            "authorName": note.author_name,
            "createdAt": isoformat(note.created_at),
        }
        for note in notes
    ]


@router.post("/{conversation_id}/notes", status_code=status.HTTP_201_CREATED)
async def create_note(
    conversation_id: str,
    payload: dict[str, str],
    auth: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, object]:
    content = payload.get("content", "")
    note = InternalNote(
        conversation_id=conversation_id,
        content=content,
        author_name=auth.name,
    )
    session.add(note)
    await session.commit()
    await session.refresh(note)

    return {
        "id": note.id,
        "conversationId": conversation_id,
        "content": note.content,
        "authorName": note.author_name,
        "createdAt": isoformat(note.created_at),
    }


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    conversation = await session.get(Conversation, conversation_id)
    if not conversation:
        return {"success": False}

    await session.delete(conversation)
    await session.commit()
    return {"success": True}

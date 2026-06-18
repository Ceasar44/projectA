import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.compat import isoformat
from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.infrastructure.db.models.conversations import Conversation, ConversationTag, Customer
from app.infrastructure.db.models.knowledge import KnowledgeEntry
from app.infrastructure.db.models.team import Ticket

router = APIRouter()


@router.get("")
async def export_data(
    type: str = Query(default="conversations"),
    format: str = Query(default="json", pattern="^(json|csv)$"),
    limit: int = Query(default=10000, ge=1, le=50000),
    from_date: str | None = Query(default=None, alias="from"),
    to_date: str | None = Query(default=None, alias="to"),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    date_filters = []
    if from_date:
        date_filters.append(datetime.fromisoformat(from_date.replace("Z", "+00:00")))
    if to_date:
        date_filters.append(datetime.fromisoformat(to_date.replace("Z", "+00:00")))

    if type == "conversations":
        query = (
            select(Conversation)
            .options(
                selectinload(Conversation.messages),
                selectinload(Conversation.tag_links).selectinload(ConversationTag.tag),
            )
            .order_by(Conversation.created_at.desc())
            .limit(limit)
        )
        if len(date_filters) >= 1:
            query = query.where(Conversation.created_at >= date_filters[0])
        if len(date_filters) == 2:
            query = query.where(Conversation.created_at <= date_filters[1])
        conversations = list((await session.scalars(query)).all())
        data = [
            {
                "id": conv.id,
                "channel": conv.channel,
                "customerName": conv.customer_name,
                "customerContact": conv.customer_contact,
                "status": conv.status,
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "createdAt": isoformat(msg.created_at),
                    }
                    for msg in conv.messages
                ],
                "createdAt": isoformat(conv.created_at),
                "updatedAt": isoformat(conv.updated_at),
                "tickets": [],
                "tags": [{"tag": {"name": link.tag.name}} for link in conv.tag_links if link.tag],
            }
            for conv in conversations
        ]
        return _stream_export(data, format, f"conversations_{datetime.now().strftime('%Y%m%d')}")

    if type == "customers":
        query = select(Customer).order_by(Customer.last_contact.desc()).limit(limit)
        if len(date_filters) >= 1:
            query = query.where(Customer.created_at >= date_filters[0])
        if len(date_filters) == 2:
            query = query.where(Customer.created_at <= date_filters[1])
        customers = list((await session.scalars(query)).all())
        data = [
            {
                "id": c.id,
                "name": c.name,
                "email": c.email,
                "phone": c.phone,
                "whatsapp": c.whatsapp,
                "tags": c.tags,
                "isBlocked": c.is_blocked,
                "firstContact": isoformat(c.first_contact),
                "lastContact": isoformat(c.last_contact),
            }
            for c in customers
        ]
        return _stream_export(data, format, f"customers_{datetime.now().strftime('%Y%m%d')}")

    if type == "tickets":
        query = (
            select(Ticket)
            .options(
                selectinload(Ticket.department),
                selectinload(Ticket.assigned_to),
                selectinload(Ticket.conversation),
            )
            .order_by(Ticket.created_at.desc())
            .limit(limit)
        )
        if len(date_filters) >= 1:
            query = query.where(Ticket.created_at >= date_filters[0])
        if len(date_filters) == 2:
            query = query.where(Ticket.created_at <= date_filters[1])
        tickets = list((await session.scalars(query)).all())
        data = [
            {
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "status": t.status,
                "priority": t.priority,
                "department": {"name": t.department.name} if t.department else None,
                "assignedTo": {"name": t.assigned_to.name} if t.assigned_to else None,
                "conversation": {"id": t.conversation_id} if t.conversation_id else None,
                "createdAt": isoformat(t.created_at),
            }
            for t in tickets
        ]
        return _stream_export(data, format, f"tickets_{datetime.now().strftime('%Y%m%d')}")

    if type == "knowledge":
        entries = list(
            (
                await session.scalars(
                    select(KnowledgeEntry).options(selectinload(KnowledgeEntry.category)).order_by(KnowledgeEntry.priority.desc()).limit(limit)
                )
            ).all()
        )
        data = [
            {
                "id": entry.id,
                "category": {"name": entry.category.name} if entry.category else None,
                "title": entry.title,
                "content": entry.content,
                "priority": entry.priority,
                "isActive": entry.is_active,
            }
            for entry in entries
        ]
        return _stream_export(data, format, f"knowledge_{datetime.now().strftime('%Y%m%d')}")

    return _stream_export(
        [{"error": "Invalid type. Supported: conversations, tickets, customers, knowledge"}],
        "json",
        "error",
    )


def _stream_export(data: list[dict[str, object]], format: str, filename: str) -> StreamingResponse:
    if format == "csv":
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=list(data[0].keys()))
            writer.writeheader()
            writer.writerows(data)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
        )

    json_str = json.dumps({"data": data, "total": len(data)}, indent=2, ensure_ascii=False)
    return StreamingResponse(
        iter([json_str]),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}.json"'},
    )

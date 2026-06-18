from datetime import datetime
from io import StringIO
import csv

from fastapi import APIRouter, Depends, Query
from fastapi.responses import ORJSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect

from app.api.deps import get_auth_context, get_session
from app.domain.auth.schemas import AuthContext
from app.infrastructure.db.models.conversations import Conversation
from app.infrastructure.db.models.knowledge import KnowledgeEntry
from app.infrastructure.db.models.team import Ticket
from sqlalchemy import select

router = APIRouter()


def serialize_row(row) -> dict[str, object]:
    payload: dict[str, object] = {}
    for column in inspect(row).mapper.column_attrs:
        value = getattr(row, column.key)
        if isinstance(value, datetime):
            payload[column.key] = value.isoformat()
        else:
            payload[column.key] = value
    return payload


@router.get("/export")
async def export_data(
    type: str = Query(default="conversations"),
    format: str = Query(default="json"),
    limit: int = Query(default=1000, ge=1, le=50000),
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
):
    model_map = {
        "conversations": Conversation,
        "tickets": Ticket,
        "knowledge": KnowledgeEntry,
    }
    model = model_map.get(type)
    if not model:
        return ORJSONResponse({"error": "Unsupported export type"}, status_code=400)
    rows = (await session.scalars(select(model).limit(limit))).all()
    data = [serialize_row(row) for row in rows]
    if format == "csv":
        headers = list(data[0].keys()) if data else []
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{type}.csv"'},
        )
    return ORJSONResponse(data)


@router.get("/realtime")
async def realtime(channel: str = Query(default="global"), _: AuthContext = Depends(get_auth_context)):
    async def event_stream():
        yield f"event: connected\ndata: {{\"type\":\"connected\",\"channel\":\"{channel}\"}}\n\n"
        yield "event: heartbeat\ndata: {\"type\":\"heartbeat\"}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

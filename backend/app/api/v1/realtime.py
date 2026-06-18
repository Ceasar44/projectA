import asyncio
import json
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from app.api.deps import get_auth_context
from app.domain.auth.schemas import AuthContext
from app.infrastructure.realtime import EventPayload, EventType, event_bus

router = APIRouter()


class SSEResponse(StreamingResponse):
    media_type = "text/event-stream"


async def event_generator(channels: list[str]):
    queue: asyncio.Queue[EventPayload] = asyncio.Queue()

    unsubscribers = []

    def on_event(event: EventPayload):
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            pass

    for channel in channels:
        unsubscribers.append(event_bus.subscribe(channel, on_event))

    try:
        yield f"data: {json.dumps({'type': 'connected', 'channel': channels[0]})}\n\n"

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30.0)
                data = {
                    "type": event.type.value,
                    "data": event.data,
                    "timestamp": event.timestamp,
                    "conversationId": event.conversation_id,
                }
                yield f"data: {json.dumps(data)}\n\n"
            except asyncio.TimeoutError:
                yield f": heartbeat\n\n"

    except asyncio.CancelledError:
        pass
    finally:
        for unsubscribe in unsubscribers:
            unsubscribe()


@router.get("")
async def subscribe_events(
    conversation_id: str | None = None,
    channel: str | None = Query(default=None),
    _: AuthContext = Depends(get_auth_context),
) -> StreamingResponse:
    channels = [channel or "global"]
    if conversation_id:
        channels.append(f"conversation:{conversation_id}")

    return SSEResponse(
        event_generator(channels),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/typing/{conversation_id}")
async def emit_typing(
    conversation_id: str,
    payload: dict[str, Any],
    _: AuthContext = Depends(get_auth_context),
) -> dict[str, bool]:
    user_name = payload.get("userName", "Agent")
    is_typing = payload.get("isTyping", True)

    event_bus.emit_typing(conversation_id, user_name, is_typing)
    return {"success": True}


@router.get("/stats")
async def get_stats(
    _: AuthContext = Depends(get_auth_context),
) -> dict[str, Any]:
    return {
        "subscriberCount": event_bus.get_subscriber_count(),
        "channelCount": event_bus.get_channel_count(),
    }

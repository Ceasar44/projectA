import asyncio
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Callable

from app.core.logging import get_logger

logger = get_logger(__name__)


class EventType(str, Enum):
    MESSAGE_NEW = "message:new"
    MESSAGE_UPDATED = "message:updated"
    CONVERSATION_NEW = "conversation:new"
    CONVERSATION_UPDATED = "conversation:updated"
    CONVERSATION_ASSIGNED = "conversation:assigned"
    TICKET_NEW = "ticket:new"
    TICKET_UPDATED = "ticket:updated"
    TYPING_START = "typing:start"
    TYPING_STOP = "typing:stop"
    AGENT_ONLINE = "agent:online"
    AGENT_OFFLINE = "agent:offline"
    NOTIFICATION = "notification"


@dataclass
class EventPayload:
    type: EventType
    data: dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    conversation_id: str | None = None


EventCallback = Callable[[EventPayload], None]


class RealtimeEventBus:
    _subscribers: dict[str, set[EventCallback]] = defaultdict(set)
    _message_queue: asyncio.Queue | None = None

    @classmethod
    def subscribe(cls, channel: str, callback: EventCallback) -> Callable[[], None]:
        cls._subscribers[channel].add(callback)

        def unsubscribe():
            subs = cls._subscribers.get(channel)
            if subs:
                subs.discard(callback)
                if not subs:
                    del cls._subscribers[channel]

        return unsubscribe

    @classmethod
    def publish(cls, channel: str, event: EventPayload) -> None:
        subs = cls._subscribers.get(channel)
        if subs:
            for callback in subs:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"SSE subscriber callback error: {e}")

        if channel != "global":
            global_subs = cls._subscribers.get("global")
            if global_subs:
                for callback in global_subs:
                    try:
                        callback(event)
                    except Exception as e:
                        logger.error(f"SSE global subscriber callback error: {e}")

    @classmethod
    def emit_new_message(
        cls,
        conversation_id: str,
        message: dict[str, Any],
    ) -> None:
        event = EventPayload(
            type=EventType.MESSAGE_NEW,
            conversation_id=conversation_id,
            data=message,
        )
        cls.publish(f"conversation:{conversation_id}", event)
        cls.publish(
            "global",
            EventPayload(
                type=EventType.MESSAGE_NEW,
                conversation_id=conversation_id,
                data={
                    "conversationId": conversation_id,
                    "messageId": message.get("id"),
                    "role": message.get("role"),
                },
            ),
        )

    @classmethod
    def emit_typing(
        cls,
        conversation_id: str,
        user_name: str,
        is_typing: bool,
    ) -> None:
        event = EventPayload(
            type=EventType.TYPING_START if is_typing else EventType.TYPING_STOP,
            conversation_id=conversation_id,
            data={"userName": user_name},
        )
        cls.publish(f"conversation:{conversation_id}", event)

    @classmethod
    def emit_conversation_update(
        cls,
        conversation_id: str,
        changes: dict[str, Any],
    ) -> None:
        event = EventPayload(
            type=EventType.CONVERSATION_UPDATED,
            conversation_id=conversation_id,
            data=changes,
        )
        cls.publish("global", event)

    @classmethod
    def emit_conversation_new(cls, conversation: dict[str, Any]) -> None:
        event = EventPayload(
            type=EventType.CONVERSATION_NEW,
            conversation_id=conversation.get("id"),
            data=conversation,
        )
        cls.publish("global", event)

    @classmethod
    def emit_ticket_new(cls, ticket: dict[str, Any]) -> None:
        event = EventPayload(
            type=EventType.TICKET_NEW,
            data=ticket,
        )
        cls.publish("global", event)

    @classmethod
    def emit_agent_status(cls, agent_id: str, agent_name: str, is_online: bool) -> None:
        event = EventPayload(
            type=EventType.AGENT_ONLINE if is_online else EventType.AGENT_OFFLINE,
            data={"agentId": agent_id, "agentName": agent_name},
        )
        cls.publish("global", event)

    @classmethod
    def emit_notification(cls, user_id: str, notification: dict[str, Any]) -> None:
        event = EventPayload(
            type=EventType.NOTIFICATION,
            data=notification,
        )
        cls.publish(f"user:{user_id}", event)

    @classmethod
    def get_subscriber_count(cls) -> int:
        return sum(len(subs) for subs in cls._subscribers.values())

    @classmethod
    def get_channel_count(cls) -> int:
        return len(cls._subscribers)


event_bus = RealtimeEventBus()

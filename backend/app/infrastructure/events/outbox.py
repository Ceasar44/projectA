from dataclasses import dataclass
from typing import Protocol

from app.infrastructure.events.types import DomainEvent


@dataclass(slots=True)
class OutboxMessage:
    topic: str
    payload: dict
    event_id: str


class OutboxRepository(Protocol):
    async def publish(self, event: DomainEvent) -> None: ...


class InMemoryOutboxRepository:
    def __init__(self) -> None:
        self.messages: list[OutboxMessage] = []

    async def publish(self, event: DomainEvent) -> None:
        self.messages.append(
            OutboxMessage(topic=event.name, payload=event.payload, event_id=event.event_id)
        )

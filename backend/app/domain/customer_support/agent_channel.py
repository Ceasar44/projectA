from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from threading import Event, RLock
from typing import TypeVar


@dataclass(frozen=True)
class AgentTurn:
    conversation_id: str
    turn_id: int


T = TypeVar("T")


class CrmAgentChannel:
    """In-memory channel adapter for CRM conversation agent runs.

    The database remains the source of truth for messages. This channel only
    coordinates volatile runtime concerns:
    - debounce bursty customer messages,
    - serialize agent runs per conversation,
    - mark older turns stale when a newer customer message arrives.
    """

    def __init__(self, debounce_seconds: float = 0.8) -> None:
        self._debounce_seconds = debounce_seconds
        self._guard = RLock()
        self._latest_turns: dict[str, int] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._active_cancel_events: dict[str, tuple[int, Event]] = {}

    def begin_turn(self, conversation_id: str) -> AgentTurn:
        with self._guard:
            turn_id = self._latest_turns.get(conversation_id, 0) + 1
            self._latest_turns[conversation_id] = turn_id
            self._locks.setdefault(conversation_id, asyncio.Lock())
            active = self._active_cancel_events.get(conversation_id)
            if active:
                _, cancel_event = active
                cancel_event.set()
            return AgentTurn(conversation_id=conversation_id, turn_id=turn_id)

    async def run_latest(
        self,
        turn: AgentTurn,
        handler: Callable[[], Awaitable[T]],
    ) -> T | None:
        lock = self._lock_for(turn.conversation_id)
        async with lock:
            await asyncio.sleep(self._debounce_seconds)
            if not self.is_latest(turn):
                return None
            cancel_event = Event()
            with self._guard:
                self._active_cancel_events[turn.conversation_id] = (turn.turn_id, cancel_event)
            try:
                result = await handler()
                if not self.is_latest(turn):
                    return None
                return result
            finally:
                with self._guard:
                    active = self._active_cancel_events.get(turn.conversation_id)
                    if active and active[0] == turn.turn_id:
                        self._active_cancel_events.pop(turn.conversation_id, None)

    def is_latest(self, turn: AgentTurn) -> bool:
        with self._guard:
            return self._latest_turns.get(turn.conversation_id) == turn.turn_id

    def cancel_event(self, turn: AgentTurn) -> Event:
        with self._guard:
            active = self._active_cancel_events.get(turn.conversation_id)
            if active and active[0] == turn.turn_id:
                return active[1]
        stale_event = Event()
        stale_event.set()
        return stale_event

    def _lock_for(self, conversation_id: str) -> asyncio.Lock:
        with self._guard:
            return self._locks.setdefault(conversation_id, asyncio.Lock())


crm_agent_channel = CrmAgentChannel()

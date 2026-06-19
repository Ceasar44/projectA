from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from threading import RLock
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

    def begin_turn(self, conversation_id: str) -> AgentTurn:
        with self._guard:
            turn_id = self._latest_turns.get(conversation_id, 0) + 1
            self._latest_turns[conversation_id] = turn_id
            self._locks.setdefault(conversation_id, asyncio.Lock())
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
            result = await handler()
            if not self.is_latest(turn):
                return None
            return result

    def is_latest(self, turn: AgentTurn) -> bool:
        with self._guard:
            return self._latest_turns.get(turn.conversation_id) == turn.turn_id

    def _lock_for(self, conversation_id: str) -> asyncio.Lock:
        with self._guard:
            return self._locks.setdefault(conversation_id, asyncio.Lock())


crm_agent_channel = CrmAgentChannel()

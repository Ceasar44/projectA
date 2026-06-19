from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.conversations import Conversation


CRM_AGENT_MEMORY_KEY = "crmAgentMemory"
MAX_MEMORY_ITEMS_PER_SCOPE = 80


@dataclass(frozen=True)
class CrmMemoryIdentity:
    business_id: str
    customer_id: str | None
    conversation_id: str


class CrmAgentMemoryService:
    """Stores CRM agent memory in existing metadata JSON fields.

    The service owns durable memory writes. Disposable extern_agent instances only
    receive a snapshot and return drafts; stale turns never commit drafts.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def build_identity(self, settings: Any, conversation: Conversation) -> CrmMemoryIdentity:
        return CrmMemoryIdentity(
            business_id=str(getattr(settings, "id", "") or getattr(settings, "business_name", "") or "default"),
            customer_id=conversation.customer_id,
            conversation_id=conversation.id,
        )

    def build_snapshot(self, conversation: Conversation) -> dict[str, Any]:
        customer_memory = []
        if conversation.customer:
            customer_memory = list((conversation.customer.metadata_json or {}).get(CRM_AGENT_MEMORY_KEY) or [])
        conversation_memory = list((conversation.metadata_json or {}).get(CRM_AGENT_MEMORY_KEY) or [])
        return {
            "customer": customer_memory[-MAX_MEMORY_ITEMS_PER_SCOPE:],
            "conversation": conversation_memory[-MAX_MEMORY_ITEMS_PER_SCOPE:],
        }

    async def commit_drafts(
        self,
        conversation: Conversation,
        drafts: list[dict[str, Any]],
        *,
        customer_message: str,
    ) -> list[dict[str, Any]]:
        committed: list[dict[str, Any]] = []
        for draft in drafts:
            normalized = self._normalize_draft(draft, conversation, customer_message)
            if not normalized:
                continue
            if normalized["scope"] == "customer" and conversation.customer:
                self._append_metadata_memory(conversation.customer, normalized)
                committed.append(normalized)
            else:
                normalized["scope"] = "conversation"
                self._append_metadata_memory(conversation, normalized)
                committed.append(normalized)
        return committed

    @staticmethod
    def _normalize_draft(
        draft: dict[str, Any],
        conversation: Conversation,
        customer_message: str,
    ) -> dict[str, Any] | None:
        content = str(draft.get("content") or "").strip()
        if not content:
            return None
        scope = str(draft.get("scope") or "conversation").strip().lower()
        if scope not in {"customer", "conversation"}:
            scope = "conversation"
        try:
            confidence = float(draft.get("confidence") or 0.7)
        except (TypeError, ValueError):
            confidence = 0.7
        confidence = max(0.0, min(1.0, confidence))
        return {
            "scope": scope,
            "kind": str(draft.get("kind") or "note").strip() or "note",
            "content": content[:1000],
            "confidence": confidence,
            "sourceConversationId": conversation.id,
            "sourceCustomerMessage": customer_message[:500],
            "createdAt": datetime.now(UTC).isoformat(),
        }

    @staticmethod
    def _append_metadata_memory(target: Any, item: dict[str, Any]) -> None:
        metadata = dict(target.metadata_json or {})
        existing = list(metadata.get(CRM_AGENT_MEMORY_KEY) or [])
        normalized_content = item["content"].casefold()
        existing = [
            memory
            for memory in existing
            if str((memory or {}).get("content") or "").casefold() != normalized_content
        ]
        metadata[CRM_AGENT_MEMORY_KEY] = [*existing, item][-MAX_MEMORY_ITEMS_PER_SCOPE:]
        target.metadata_json = metadata

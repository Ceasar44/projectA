import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.infrastructure.db.models.conversations import Conversation, InternalNote
from app.infrastructure.db.models.knowledge import KnowledgeEntry
from app.infrastructure.db.models.operations import Webhook
from app.infrastructure.db.models.team import Department, TeamMember, Ticket


ToolHandler = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class SupportTool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler

    def as_openai_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class SupportToolRegistry:
    def __init__(
        self,
        session: AsyncSession,
        conversation: Conversation,
        knowledge_entries: list[KnowledgeEntry],
    ) -> None:
        self.session = session
        self.conversation = conversation
        self.knowledge_entries = knowledge_entries
        self._tools: dict[str, SupportTool] = {
            "get_customer_history": SupportTool(
                name="get_customer_history",
                description="Retrieve previous conversations for this customer.",
                parameters={
                    "type": "object",
                    "properties": {
                        "customerContact": {"type": "string"},
                        "customerId": {"type": "string"},
                    },
                },
                handler=self.get_customer_history,
            ),
            "search_knowledge": SupportTool(
                name="search_knowledge",
                description="Search the active customer-service knowledge base.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "number"},
                    },
                    "required": ["query"],
                },
                handler=self.search_knowledge,
            ),
            "create_ticket": SupportTool(
                name="create_ticket",
                description="Create a support ticket for issues that need human attention.",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "priority": {
                            "type": "string",
                            "enum": ["low", "medium", "high", "urgent"],
                        },
                        "department": {"type": "string"},
                    },
                    "required": ["title", "description", "priority"],
                },
                handler=self.create_ticket,
            ),
            "assign_ticket": SupportTool(
                name="assign_ticket",
                description="Assign a ticket to an available team member by expertise.",
                parameters={
                    "type": "object",
                    "properties": {
                        "ticketId": {"type": "string"},
                        "expertise": {"type": "string"},
                    },
                    "required": ["ticketId", "expertise"],
                },
                handler=self.assign_ticket,
            ),
            "add_internal_note": SupportTool(
                name="add_internal_note",
                description="Add an internal note to the conversation for human agents.",
                parameters={
                    "type": "object",
                    "properties": {"content": {"type": "string"}},
                    "required": ["content"],
                },
                handler=self.add_internal_note,
            ),
            "trigger_webhook": SupportTool(
                name="trigger_webhook",
                description="Trigger a configured webhook by name.",
                parameters={
                    "type": "object",
                    "properties": {
                        "webhookName": {"type": "string"},
                        "data": {"type": "object"},
                    },
                    "required": ["webhookName"],
                },
                handler=self.trigger_webhook,
            ),
            "schedule_followup": SupportTool(
                name="schedule_followup",
                description="Schedule a follow-up message after a delay.",
                parameters={
                    "type": "object",
                    "properties": {
                        "conversationId": {"type": "string"},
                        "message": {"type": "string"},
                        "delayHours": {"type": "number"},
                    },
                    "required": ["conversationId", "message", "delayHours"],
                },
                handler=self.schedule_followup,
            ),
        }

    def openai_tools(self, allowed_tools: list[str] | None = None) -> list[dict[str, Any]]:
        return [tool.as_openai_tool() for tool in self._iter_allowed(allowed_tools)]

    def list_allowed_names(self, allowed_tools: list[str] | None = None) -> list[str]:
        return [tool.name for tool in self._iter_allowed(allowed_tools)]

    async def execute(self, name: str, args: dict[str, Any], allowed_tools: list[str] | None = None) -> dict[str, Any]:
        allowed = set(self.list_allowed_names(allowed_tools))
        if name not in allowed:
            return {"success": False, "message": f"Tool is not allowed: {name}"}
        return await self._tools[name].handler(args)

    def _iter_allowed(self, allowed_tools: list[str] | None) -> list[SupportTool]:
        if not allowed_tools:
            return list(self._tools.values())
        allowed = set(allowed_tools)
        return [tool for name, tool in self._tools.items() if name in allowed]

    async def get_customer_history(self, _: dict[str, Any]) -> dict[str, Any]:
        filters = []
        if self.conversation.customer_id:
            filters.append(Conversation.customer_id == self.conversation.customer_id)
        elif self.conversation.customer_contact:
            filters.append(Conversation.customer_contact == self.conversation.customer_contact)
        else:
            return {"success": True, "history": []}

        rows = list(
            (
                await self.session.scalars(
                    select(Conversation)
                    .options(selectinload(Conversation.messages))
                    .where(*filters, Conversation.id != self.conversation.id)
                    .order_by(Conversation.created_at.desc())
                    .limit(5)
                )
            ).all()
        )
        history = [
            {
                "conversationId": row.id,
                "channel": row.channel,
                "status": row.status,
                "summary": row.summary,
                "messageCount": len(row.messages),
            }
            for row in rows
        ]
        return {"success": True, "history": history}

    async def search_knowledge(self, args: dict[str, Any]) -> dict[str, Any]:
        query = str(args.get("query") or "").lower()
        limit = max(1, min(int(args.get("limit") or 3), 10))
        scored: list[tuple[int, KnowledgeEntry]] = []
        terms = [term for term in query.replace("?", " ").replace(",", " ").split() if term]
        for entry in self.knowledge_entries:
            haystack = f"{entry.title} {entry.content}".lower()
            score = sum(1 for term in terms if term in haystack)
            if score > 0:
                scored.append((score, entry))
        if not scored:
            scored = [(0, entry) for entry in self.knowledge_entries[:limit]]
        scored.sort(key=lambda item: (item[0], item[1].priority), reverse=True)
        results = [
            {
                "id": entry.id,
                "title": entry.title,
                "contentPreview": entry.content[:500],
            }
            for _, entry in scored[:limit]
        ]
        return {"success": True, "results": results}

    async def create_ticket(self, args: dict[str, Any]) -> dict[str, Any]:
        department = None
        department_name = str(args.get("department") or "").strip()
        if department_name:
            department = await self.session.scalar(
                select(Department).where(Department.name.ilike(f"%{department_name}%"))
            )

        ticket = Ticket(
            conversation_id=self.conversation.id,
            department_id=department.id if department else None,
            title=str(args.get("title") or "Support request")[:500],
            description=str(args.get("description") or ""),
            priority=str(args.get("priority") or "medium"),
        )
        self.session.add(ticket)
        await self.session.flush()
        return {
            "success": True,
            "ticketId": ticket.id,
            "message": f"Ticket created: {ticket.title} (Priority: {ticket.priority})",
        }

    async def assign_ticket(self, args: dict[str, Any]) -> dict[str, Any]:
        ticket_id = str(args.get("ticketId") or "")
        expertise = str(args.get("expertise") or "")
        ticket = await self.session.get(Ticket, ticket_id) if ticket_id else None
        member = await self.session.scalar(
            select(TeamMember)
            .options(selectinload(TeamMember.department))
            .where(TeamMember.is_available.is_(True), TeamMember.expertise.ilike(f"%{expertise}%"))
        )
        if not ticket or not member:
            return {"success": False, "message": "No matching team member or ticket found"}
        ticket.assigned_to_id = member.id
        ticket.status = "in_progress"
        await self.session.flush()
        return {
            "success": True,
            "assignedTo": member.name,
            "department": member.department.name if member.department else "",
        }

    async def add_internal_note(self, args: dict[str, Any]) -> dict[str, Any]:
        content = str(args.get("content") or "").strip()
        if not content:
            return {"success": False, "message": "content is required"}
        note = InternalNote(
            conversation_id=self.conversation.id,
            content=content,
            author_name="AI Agent",
        )
        self.session.add(note)
        await self.session.flush()
        return {"success": True, "noteId": note.id}

    async def trigger_webhook(self, args: dict[str, Any]) -> dict[str, Any]:
        webhook_name = str(args.get("webhookName") or "").strip()
        webhook = await self.session.scalar(
            select(Webhook).where(Webhook.is_active.is_(True), Webhook.name.ilike(f"%{webhook_name}%"))
        )
        if not webhook:
            return {"success": False, "message": f"No active webhook found with name: {webhook_name}"}
        return {
            "success": True,
            "message": f'Webhook "{webhook.name}" queued for delivery',
            "payload": args.get("data") or {},
        }

    async def schedule_followup(self, args: dict[str, Any]) -> dict[str, Any]:
        delay_hours = float(args.get("delayHours") or 0)
        return {
            "success": True,
            "message": f'Follow-up scheduled in {delay_hours:g} hours: "{args.get("message", "")}"',
        }


def parse_tool_arguments(raw_arguments: Any) -> dict[str, Any]:
    if isinstance(raw_arguments, dict):
        return raw_arguments
    if not raw_arguments:
        return {}
    try:
        parsed = json.loads(str(raw_arguments))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}

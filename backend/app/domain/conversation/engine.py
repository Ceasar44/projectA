from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.infrastructure.db.models.conversations import Conversation, ConversationTag, InternalNote, Message, Tag
from app.infrastructure.db.models.operations import SLARule
from app.infrastructure.db.models.team import Department, TeamMember, Ticket

logger = get_logger(__name__)


class RoutingStrategy(str, Enum):
    ROUND_ROBIN = "round_robin"
    LEAST_BUSY = "least_busy"
    SKILL_BASED = "skill_based"
    PRIORITY = "priority"


@dataclass
class RoutingResult:
    assigned_to_id: str
    assigned_to_name: str
    department_id: str
    department_name: str
    reason: str


class ConversationEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def route_conversation(
        self,
        conversation_id: str,
        strategy: RoutingStrategy = RoutingStrategy.SKILL_BASED,
        required_expertise: str | None = None,
        department_id: str | None = None,
    ) -> RoutingResult | None:
        filters: dict[str, Any] = {"is_available": True}
        if department_id:
            filters["department_id"] = department_id

        stmt = (
            select(TeamMember)
            .options(selectinload(TeamMember.department))
            .where(TeamMember.is_available == True)
            .order_by(TeamMember.created_at.asc())
        )
        if department_id:
            stmt = stmt.where(TeamMember.department_id == department_id)

        members = list((await self.session.scalars(stmt)).all())
        if not members:
            return None

        selected = None

        if strategy == RoutingStrategy.SKILL_BASED:
            if required_expertise:
                expertise_lower = required_expertise.lower()
                for m in members:
                    if expertise_lower in m.expertise.lower():
                        selected = m
                        break
            if not selected:
                selected = members[0]

        elif strategy == RoutingStrategy.LEAST_BUSY:
            ticket_counts = {}
            for m in members:
                count = await self.session.scalar(
                    select(func.count()).select_from(Ticket).where(Ticket.assigned_to_id == m.id)
                )
                ticket_counts[m.id] = count or 0
            selected = min(members, key=lambda m: ticket_counts[m.id])

        elif strategy == RoutingStrategy.ROUND_ROBIN:
            last_ticket = await self.session.scalar(
                select(Ticket)
                .where(Ticket.assigned_to_id.isnot(None))
                .order_by(Ticket.created_at.desc())
            )
            if last_ticket and last_ticket.assigned_to_id:
                member_ids = [m.id for m in members]
                try:
                    last_index = member_ids.index(last_ticket.assigned_to_id)
                    selected = members[(last_index + 1) % len(members)]
                except ValueError:
                    selected = members[0]
            else:
                selected = members[0]

        else:
            selected = members[0]

        if not selected:
            return None

        return RoutingResult(
            assigned_to_id=selected.id,
            assigned_to_name=selected.name,
            department_id=selected.department_id,
            department_name=selected.department.name if selected.department else "",
            reason=f"Routed via {strategy.value} strategy",
        )

    async def transfer_conversation(
        self,
        conversation_id: str,
        to_member_id: str,
        from_member_name: str,
        note: str | None = None,
    ) -> bool:
        member = await self.session.get(TeamMember, to_member_id)
        if not member:
            return False

        await self.session.execute(
            select(Ticket)
            .where(
                Ticket.conversation_id == conversation_id,
                Ticket.status.in_(["open", "in_progress"]),
            )
        )
        tickets = list(
            (await self.session.scalars(
                select(Ticket).where(
                    Ticket.conversation_id == conversation_id,
                    Ticket.status.in_(["open", "in_progress"]),
                )
            )).all()
        )
        for ticket in tickets:
            ticket.assigned_to_id = to_member_id

        content = f"Conversation transferred from {from_member_name} to {member.name}"
        if note:
            content += f": {note}"

        internal_note = InternalNote(
            conversation_id=conversation_id,
            content=content,
            author_name="System",
        )
        self.session.add(internal_note)
        await self.session.commit()

        logger.info(
            "Conversation transferred",
            extra={
                "conversation_id": conversation_id,
                "from": from_member_name,
                "to": member.name,
            },
        )
        return True

    async def merge_conversations(self, primary_id: str, secondary_id: str) -> bool:
        primary = await self.session.get(Conversation, primary_id)
        secondary = await self.session.get(Conversation, secondary_id)

        if not primary or not secondary:
            return False

        messages = list(
            (await self.session.scalars(
                select(Message).where(Message.conversation_id == secondary_id)
            )).all()
        )
        for msg in messages:
            msg.conversation_id = primary_id

        tickets = list(
            (await self.session.scalars(
                select(Ticket).where(Ticket.conversation_id == secondary_id)
            )).all()
        )
        for ticket in tickets:
            ticket.conversation_id = primary_id

        notes = list(
            (await self.session.scalars(
                select(InternalNote).where(InternalNote.conversation_id == secondary_id)
            )).all()
        )
        for n in notes:
            n.conversation_id = primary_id

        merge_note = InternalNote(
            conversation_id=primary_id,
            content=f"Merged with conversation {secondary_id} ({secondary.customer_name} via {secondary.channel})",
            author_name="System",
        )
        self.session.add(merge_note)

        secondary.status = "closed"
        secondary.summary = f"Merged into {primary_id}"

        await self.session.commit()
        return True

    async def snooze_conversation(
        self,
        conversation_id: str,
        snooze_until: datetime,
        reason: str,
        author_name: str,
    ) -> bool:
        conversation = await self.session.get(Conversation, conversation_id)
        if not conversation:
            return False

        conversation.status = "snoozed"
        conversation.metadata_json = {
            **(conversation.metadata_json or {}),
            "snoozeUntil": snooze_until.isoformat(),
            "snoozeReason": reason,
        }

        note = InternalNote(
            conversation_id=conversation_id,
            content=f"Snoozed until {snooze_until.strftime('%Y-%m-%d %H:%M')}: {reason}",
            author_name=author_name,
        )
        self.session.add(note)
        await self.session.commit()
        return True

    async def check_sla_breaches(self) -> int:
        rules = list(
            (await self.session.scalars(
                select(SLARule).where(SLARule.is_active == True)
            )).all()
        )

        if not rules:
            return 0

        escalated = 0

        for rule in rules:
            cutoff = datetime.now(UTC) - timedelta(minutes=rule.first_response_mins)

            stmt = (
                select(Conversation)
                .where(
                    Conversation.status == "active",
                    Conversation.created_at <= cutoff,
                )
                .options(selectinload(Conversation.messages))
            )

            if rule.channel != "all":
                stmt = stmt.where(Conversation.channel == rule.channel)

            conversations = list((await self.session.scalars(stmt)).all())

            for conv in conversations:
                has_response = any(m.role == "assistant" for m in conv.messages)
                if not has_response:
                    conv.status = "escalated"
                    escalated += 1

        if escalated > 0:
            await self.session.commit()
            logger.warning(f"SLA breach: {escalated} conversations auto-escalated")

        return escalated

    async def execute_macro(
        self,
        conversation_id: str,
        actions: list[dict[str, str]],
        author_name: str,
    ) -> tuple[int, list[str]]:
        executed = 0
        errors: list[str] = []

        for action in actions:
            action_type = action.get("type", "")
            value = action.get("value", "")

            try:
                if action_type == "set_status":
                    conversation = await self.session.get(Conversation, conversation_id)
                    if conversation:
                        conversation.status = value
                        executed += 1

                elif action_type == "assign_department":
                    dept = await self.session.scalar(
                        select(Department).where(Department.name.ilike(f"%{value}%"))
                    )
                    if dept:
                        tickets = list(
                            (await self.session.scalars(
                                select(Ticket).where(Ticket.conversation_id == conversation_id)
                            )).all()
                        )
                        for ticket in tickets:
                            ticket.department_id = dept.id
                        executed += 1

                elif action_type == "add_tag":
                    conversation = await self.session.get(Conversation, conversation_id)
                    if conversation:
                        tag = await self.session.scalar(select(Tag).where(Tag.name == value))
                        if not tag:
                            tag = Tag(name=value)
                            self.session.add(tag)
                            await self.session.flush()
                        existing = await self.session.scalar(
                            select(ConversationTag).where(
                                ConversationTag.conversation_id == conversation_id,
                                ConversationTag.tag_id == tag.id,
                            )
                        )
                        if not existing:
                            self.session.add(ConversationTag(conversation_id=conversation_id, tag_id=tag.id))
                        executed += 1

                elif action_type == "add_note":
                    note = InternalNote(
                        conversation_id=conversation_id,
                        content=value,
                        author_name=author_name,
                    )
                    self.session.add(note)
                    executed += 1

                elif action_type == "send_message":
                    message = Message(
                        conversation_id=conversation_id,
                        role="assistant",
                        content=value,
                    )
                    self.session.add(message)
                    executed += 1

                else:
                    errors.append(f"Unknown action type: {action_type}")

            except Exception as e:
                errors.append(f"{action_type}: {str(e)}")

        await self.session.commit()
        return executed, errors

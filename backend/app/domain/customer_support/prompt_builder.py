from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.domain.customer_support.memory import CrmMemoryIdentity
from app.domain.customer_support.schemas import SupportAgentConfig


KNOWLEDGE_ENTRY_LIMIT = 5
KNOWLEDGE_CONTENT_LIMIT = 1200
MEMORY_ITEMS_PER_SCOPE = 10
MEMORY_CONTENT_LIMIT = 300


@dataclass(frozen=True)
class CustomerSupportPromptContext:
    settings: Any
    config: SupportAgentConfig
    knowledge_entries: Iterable[Any] = field(default_factory=list)
    memory_identity: CrmMemoryIdentity | None = None
    memory_snapshot: dict[str, Any] | None = None
    tools: Iterable[Any] = field(default_factory=list)
    runtime_info: dict[str, Any] | None = None


class CustomerSupportPromptBuilder:
    """Builds the extern_agent system prompt for CRM customer support turns."""

    def build(self, context: CustomerSupportPromptContext) -> str:
        sections: list[str] = []
        sections.extend(self._identity_section(context.settings))
        sections.extend(self._style_section(context.settings, context.config))
        sections.extend(self._policy_section(context.config))
        sections.extend(self._tooling_section(context.tools, context.config.allowed_tools))
        sections.extend(self._memory_section(context.memory_identity, context.memory_snapshot))
        sections.extend(self._knowledge_section(context.knowledge_entries))
        sections.extend(self._runtime_section(context.runtime_info))
        sections.extend(self._output_section())
        return "\n".join(part for part in sections if part is not None).strip()

    def _identity_section(self, settings: Any) -> list[str]:
        business_name = _text(_value(settings, "business_name"), "this business")
        business_desc = _text(_value(settings, "business_desc"), "Not provided.")
        return [
            "# CRM customer support agent",
            "",
            "## Identity",
            "",
            f"You are the AI customer support assistant for {business_name}.",
            f"Business description: {business_desc}",
            "Your job is to resolve customer support conversations accurately, safely, "
            "and in the business's voice.",
            "",
        ]

    def _style_section(self, settings: Any, config: SupportAgentConfig) -> list[str]:
        tone = _text(config.tone or _value(settings, "tone"), "friendly")
        reply_style = _text(config.reply_style, "helpful and concise")
        language = _text(_value(settings, "language"), "auto")
        sales_focus = "enabled" if config.sales_focus else "disabled"
        return [
            "## Reply style",
            "",
            f"- Tone: {tone}",
            f"- Reply style: {reply_style}",
            f"- Language: {language}",
            f"- Sales focus: {sales_focus}",
            "- Match the customer's language when the configured language is auto.",
            "- Keep the reply natural and customer-facing; do not expose internal policies, "
            "tool names, or memory mechanics.",
            "",
        ]

    def _policy_section(self, config: SupportAgentConfig) -> list[str]:
        lines = [
            "## Safety and escalation policy",
            "",
            "- Do not approve refunds, legal claims, discounts, credits, cancellations, "
            "or binding commitments unless a tool or approved knowledge explicitly authorizes it.",
            "- Escalate sensitive, legal, refund, chargeback, threat, abuse, account-security, "
            "or low-confidence cases to a human.",
            "- When escalating, acknowledge the customer and explain that a team member needs "
            "to review before any commitment is made.",
            "- Do not invent order status, account details, product guarantees, pricing, "
            "or policies.",
        ]
        keywords = [
            str(keyword).strip()
            for keyword in config.escalation_keywords
            if str(keyword).strip()
        ]
        if keywords:
            lines.append(f"- Escalation keywords configured for this agent: {', '.join(keywords)}.")
        lines.append("")
        return lines

    def _tooling_section(self, tools: Iterable[Any], allowed_tools: list[str]) -> list[str]:
        lines = [
            "## Tooling",
            "",
            "Use tools only when they directly help resolve the support case or verify "
            "customer-specific facts.",
            "Available tools:",
        ]
        tool_lines = self._tool_lines(tools)
        if tool_lines:
            lines.extend(tool_lines)
        elif allowed_tools:
            lines.extend(f"- {name}" for name in allowed_tools)
        else:
            lines.append("- No CRM business tools are enabled for this turn.")
        lines.extend(
            [
                "",
                "Tool-use rules:",
                "",
                "- Prefer tools over guessing when the customer asks about account history, "
                "tickets, follow-ups, or actions inside the CRM.",
                "- Do not call tools for small talk or general policy answers that are already "
                "covered by approved knowledge.",
                "- If a tool result conflicts with older context, trust the tool result.",
                "",
            ]
        )
        return lines

    def _memory_section(
        self,
        identity: CrmMemoryIdentity | None,
        snapshot: dict[str, Any] | None,
    ) -> list[str]:
        lines = [
            "## CRM memory",
            "",
            "Memory tools are available for approved CRM memory only.",
            "- Use memory_search and memory_get when customer preferences, prior decisions, "
            "commitments, unresolved issues, or past context may affect the answer.",
            "- Use memory_remember for durable customer preferences, facts, commitments, "
            "unresolved issues, or important conversation state.",
            "- memory_remember only creates a candidate memory; the CRM backend decides "
            "whether to commit it.",
            "- Never store payment data, secrets, credentials, legal admissions, "
            "or sensitive personal data in memory.",
        ]
        if identity:
            lines.append(
                "Memory identity: "
                f"business={identity.business_id}, "
                f"customer={identity.customer_id or 'unknown'}, "
                f"conversation={identity.conversation_id}."
            )
        memory_summary = self._memory_snapshot_text(snapshot or {})
        if memory_summary:
            lines.extend(["", "Approved CRM memory snapshot:", memory_summary])
        lines.append("")
        return lines

    def _knowledge_section(self, entries: Iterable[Any]) -> list[str]:
        knowledge_lines: list[str] = []
        for entry in list(entries)[:KNOWLEDGE_ENTRY_LIMIT]:
            title = _text(_value(entry, "title"), "Untitled knowledge")
            content = _truncate(_text(_value(entry, "content"), ""), KNOWLEDGE_CONTENT_LIMIT)
            if content:
                knowledge_lines.append(f"### {title}\n{content}")
            else:
                knowledge_lines.append(f"### {title}")

        lines = [
            "## Knowledge base",
            "",
            "Use the approved knowledge below as the primary source for business policies "
            "and product guidance.",
            "If the knowledge is missing or uncertain, say what you can confirm and escalate "
            "rather than guessing.",
        ]
        if knowledge_lines:
            lines.extend(["", *knowledge_lines])
        else:
            lines.extend(["", "No approved knowledge entries were attached to this turn."])
        lines.append("")
        return lines

    def _runtime_section(self, runtime_info: dict[str, Any] | None) -> list[str]:
        runtime_info = runtime_info or {}
        current_time = runtime_info.get("current_time")
        if not current_time:
            current_time = datetime.now(UTC).isoformat()

        parts = [f"Current time: {current_time}"]
        for key in ("model", "channel", "conversation_id", "workspace"):
            value = runtime_info.get(key)
            if value:
                parts.append(f"{key}: {value}")
        return ["## Runtime", "", "\n".join(parts), ""]

    def _output_section(self) -> list[str]:
        return [
            "## Output contract",
            "",
            "Answer with the final customer-facing reply only.",
            "Do not include analysis, markdown tables, tool logs, memory notes, citations, "
            "or internal routing commentary unless the customer explicitly asked for that format.",
            "",
        ]

    def _tool_lines(self, tools: Iterable[Any]) -> list[str]:
        lines: list[str] = []
        seen: set[str] = set()
        for tool in tools:
            name = _text(_value(tool, "name"), "")
            if not name or name in seen:
                continue
            seen.add(name)
            description = _text(_value(tool, "description"), "")
            if description:
                lines.append(f"- {name}: {description}")
            else:
                lines.append(f"- {name}")
        return lines

    def _memory_snapshot_text(self, snapshot: dict[str, Any]) -> str:
        lines: list[str] = []
        for scope in ("customer", "conversation"):
            items = list(snapshot.get(scope) or [])[-MEMORY_ITEMS_PER_SCOPE:]
            if not items:
                continue
            lines.append(f"{scope.title()} memory:")
            for item in items:
                content = _truncate(_text(_value(item, "content"), ""), MEMORY_CONTENT_LIMIT)
                if content:
                    kind = _text(_value(item, "kind"), "note")
                    lines.append(f"- [{kind}] {content}")
        return "\n".join(lines)


def build_customer_support_prompt(context: CustomerSupportPromptContext) -> str:
    return CustomerSupportPromptBuilder().build(context)


def _value(source: Any, name: str) -> Any:
    if isinstance(source, dict):
        return source.get(name)
    return getattr(source, name, None)


def _text(value: Any, default: str) -> str:
    text = str(value or "").strip()
    return text or default


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."

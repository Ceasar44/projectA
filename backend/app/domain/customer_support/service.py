import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.automation.service import AutomationService
from app.domain.conversation.schemas import MessageCreate
from app.domain.conversation.service import ConversationService
from app.domain.customer_support.agent_channel import AgentTurn, crm_agent_channel
from app.domain.customer_support.schemas import SupportAgentConfig, SupportAgentResult
from app.domain.customer_support.tools import SupportToolRegistry, parse_tool_arguments
from app.domain.tokens.service import TokenService
from app.infrastructure.db.models.conversations import Conversation, Message
from app.infrastructure.db.models.knowledge import KnowledgeEntry
from app.infrastructure.db.models.operations import AiAutoReplyLog, AiCustomerServiceConfig, Settings
from app.infrastructure.db.repositories.automation import AutomationRuleRepository
from app.infrastructure.db.repositories.conversations import ConversationRepository, MessageRepository
from app.infrastructure.db.repositories.customers import CustomerRepository
from app.infrastructure.db.repositories.settings import SettingsRepository
from app.infrastructure.db.unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.integrations.ai import OpenAIProvider
from app.infrastructure.integrations.extern_agent_adapter import CrmExternAgentAdapter


DEFAULT_ALLOWED_TOOLS = [
    "get_customer_history",
    "search_knowledge",
    "create_ticket",
    "assign_ticket",
    "add_internal_note",
    "trigger_webhook",
    "schedule_followup",
]


def analyze_sentiment(message: str) -> str:
    lowered = message.lower()
    negative_terms = [
        "angry",
        "refund",
        "terrible",
        "broken",
        "hate",
        "complaint",
        "lawsuit",
        "attorney",
        "not working",
    ]
    positive_terms = ["thanks", "great", "awesome", "love", "perfect"]
    if any(term in lowered for term in negative_terms):
        return "negative"
    if any(term in lowered for term in positive_terms):
        return "positive"
    return "neutral"


def detect_intent(message: str) -> str:
    lowered = message.lower()
    intent_map = {
        "refund": ["refund", "chargeback", "money back", "dispute"],
        "billing": ["invoice", "billing", "payment", "charged"],
        "technical_support": ["error", "bug", "broken", "issue", "problem", "not working"],
        "account": ["login", "password", "account", "sign in"],
        "human_handoff": ["human", "agent", "manager", "person", "attorney", "lawsuit"],
    }
    for intent, keywords in intent_map.items():
        if any(keyword in lowered for keyword in keywords):
            return intent
    return "general_support"


def requires_human_approval(message: str, escalation_keywords: list[str] | None = None) -> dict[str, str | bool]:
    lowered = message.lower()
    configured = [str(keyword).lower() for keyword in escalation_keywords or []]
    for keyword in configured:
        if keyword and keyword in lowered:
            return {"required": True, "reason": f"Matched escalation keyword: {keyword}"}

    escalation_terms = {
        "legal_risk": ["lawsuit", "legal", "attorney"],
        "refund_or_chargeback": ["refund", "chargeback", "dispute"],
        "explicit_handoff": ["human", "manager", "agent", "person"],
        "high_urgency": ["urgent", "asap", "immediately", "critical"],
    }
    for reason, keywords in escalation_terms.items():
        if any(keyword in lowered for keyword in keywords):
            return {"required": True, "reason": reason}
    return {"required": False, "reason": ""}


def estimate_confidence(
    response: str,
    knowledge_count: int,
    used_tools: bool,
    provider_status: str,
    escalated: bool,
) -> float:
    score = 0.86
    if provider_status and provider_status != "ok":
        score -= 0.22
    if knowledge_count == 0:
        score -= 0.12
    if escalated:
        score -= 0.2
    if "not configured" in response.lower() or "could not" in response.lower():
        score -= 0.18
    if used_tools:
        score += 0.05
    return round(max(0.0, min(1.0, score)), 2)


class CustomerSupportAgentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.token_service = TokenService(session)

    async def reply_to_conversation(
        self,
        conversation_id: str,
        customer_message: str,
        *,
        config: SupportAgentConfig | None = None,
        source: str = "chat_api",
        write_auto_reply_log: bool = False,
    ) -> SupportAgentResult:
        settings = await SettingsRepository(self.session).get_default()
        conversation = await self._load_conversation(conversation_id)
        if not conversation:
            return SupportAgentResult(
                conversation_id=conversation_id,
                reply="Conversation not found.",
                status="escalated",
                confidence=0.0,
                intent="unknown",
                sentiment="neutral",
                escalation_reason="conversation_not_found",
            )

        config = config or SupportAgentConfig(
            tone=settings.tone,
            reply_style="helpful and concise",
            sales_focus=True,
            allowed_tools=DEFAULT_ALLOWED_TOOLS,
        )
        if not config.allowed_tools:
            config.allowed_tools = list(DEFAULT_ALLOWED_TOOLS)

        turn = crm_agent_channel.begin_turn(conversation.id)
        result = await crm_agent_channel.run_latest(
            turn,
            lambda: self._reply_to_latest_turn(
                conversation_id=conversation.id,
                customer_message=customer_message,
                settings=settings,
                config=config,
                source=source,
                write_auto_reply_log=write_auto_reply_log,
                turn=turn,
            ),
        )
        return result or self._superseded_result(conversation.id)

    async def _reply_to_latest_turn(
        self,
        *,
        conversation_id: str,
        customer_message: str,
        settings: Settings,
        config: SupportAgentConfig,
        source: str,
        write_auto_reply_log: bool,
        turn: AgentTurn,
    ) -> SupportAgentResult:
        conversation = await self._load_conversation(conversation_id)
        if not conversation:
            return self._superseded_result(conversation_id, reason="conversation_not_found")

        sentiment = analyze_sentiment(customer_message)
        intent = detect_intent(customer_message)
        approval = requires_human_approval(customer_message, config.escalation_keywords)
        escalation_reason = str(approval["reason"] if approval["required"] else "")

        automation_matches = await self._evaluate_automations(conversation, customer_message)
        knowledge_entries = await self._load_knowledge_entries(config.knowledge_entry_ids)
        sources = self._sources_from_entries(knowledge_entries)
        registry = SupportToolRegistry(self.session, conversation, knowledge_entries)
        tool_calls: list[dict[str, Any]] = []

        if not approval["required"] and crm_agent_channel.is_latest(turn):
            tool_calls.extend(await self._run_heuristic_tools(registry, customer_message, intent, config.allowed_tools))

        if not crm_agent_channel.is_latest(turn):
            return self._superseded_result(conversation.id, intent=intent, sentiment=sentiment)

        if approval["required"]:
            reply = self._handoff_reply(settings, escalation_reason)
            ai_response = {"status": "policy_escalated", "usage": {}, "toolCalls": []}
        else:
            reply, ai_response, model_tool_calls = await self._run_model_turn(
                settings,
                conversation,
                customer_message,
                config,
                registry,
                knowledge_entries,
                turn=turn,
            )
            tool_calls.extend(model_tool_calls)

        if not crm_agent_channel.is_latest(turn):
            return self._superseded_result(conversation.id, intent=intent, sentiment=sentiment)

        provider_status = str(ai_response.get("status") or "")
        status = "escalated" if approval["required"] else "sent"
        confidence = estimate_confidence(
            reply,
            len(knowledge_entries),
            bool(tool_calls),
            provider_status,
            status == "escalated",
        )
        if confidence < 0.45 and status != "escalated":
            status = "escalated"
            escalation_reason = escalation_reason or "low_confidence"

        usage = ai_response.get("usage") or {}
        total_tokens = int(usage.get("total_tokens") or 0)
        if total_tokens <= 0:
            total_tokens = self.token_service.estimate_tokens(customer_message, reply)

        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=reply,
            tool_calls={"calls": tool_calls, "sources": sources} if tool_calls or sources else None,
        )
        self.session.add(assistant_message)

        await self.token_service.record_consumption(
            total_tokens,
            source,
            f"AI customer support response for conversation {conversation.id}",
            {
                "conversationId": conversation.id,
                "providerStatus": provider_status,
                "status": status,
                "intent": intent,
                "confidence": confidence,
            },
            reference_id=conversation.id,
        )

        if write_auto_reply_log:
            self.session.add(
                AiAutoReplyLog(
                    conversation_id=conversation.id,
                    customer_id=conversation.customer_id,
                    config_scope=config.config_scope,
                    knowledge_entry_ids=[entry.id for entry in knowledge_entries],
                    customer_message=customer_message,
                    ai_reply=reply if status == "sent" else "",
                    status=status,
                    escalation_reason=escalation_reason,
                    usage_total_tokens=total_tokens,
                    intent=intent,
                    sentiment=sentiment,
                    confidence=confidence,
                    tool_calls=tool_calls,
                    sources=sources,
                    agent_status=status,
                )
            )

        conversation.status = "escalated" if status == "escalated" else conversation.status
        conversation.metadata_json = {
            **(conversation.metadata_json or {}),
            "sentiment": sentiment,
            "intent": intent,
            "escalationReason": escalation_reason,
            "providerStatus": provider_status,
            "confidence": confidence,
            "automationMatches": automation_matches,
            "toolCallCount": len(tool_calls),
            "sources": sources,
        }

        await self.session.commit()
        await self.session.refresh(assistant_message)

        return SupportAgentResult(
            conversation_id=conversation.id,
            reply=reply,
            status=status,
            confidence=confidence,
            intent=intent,
            sentiment=sentiment,
            escalation_reason=escalation_reason,
            tool_calls=tool_calls,
            sources=sources,
            provider_status=provider_status,
            usage=usage,
            assistant_message={
                "id": assistant_message.id,
                "conversationId": assistant_message.conversation_id,
                "role": assistant_message.role,
                "content": assistant_message.content,
                "createdAt": assistant_message.created_at.isoformat()
                if assistant_message.created_at
                else None,
            },
            automation_matches=automation_matches,
        )

    @staticmethod
    def _superseded_result(
        conversation_id: str,
        *,
        intent: str = "superseded",
        sentiment: str = "neutral",
        reason: str = "superseded_by_newer_message",
    ) -> SupportAgentResult:
        return SupportAgentResult(
            conversation_id=conversation_id,
            reply="",
            status="superseded",
            confidence=0.0,
            intent=intent,
            sentiment=sentiment,
            escalation_reason=reason,
            provider_status="superseded",
        )

    async def get_active_auto_reply_config(self, conversation: Conversation) -> SupportAgentConfig | None:
        global_config = await self.session.scalar(
            select(AiCustomerServiceConfig).where(AiCustomerServiceConfig.scope == "global")
        )
        customer_config = None
        if conversation.customer_id:
            customer_config = await self.session.scalar(
                select(AiCustomerServiceConfig).where(
                    AiCustomerServiceConfig.scope == "customer",
                    AiCustomerServiceConfig.customer_id == conversation.customer_id,
                )
            )
        active = customer_config if customer_config and customer_config.enabled else global_config
        if not active or not active.enabled:
            return None
        return SupportAgentConfig(
            config_scope=active.scope,
            tone=active.tone,
            reply_style=active.reply_style,
            sales_focus=active.sales_focus,
            knowledge_entry_ids=list(active.knowledge_entry_ids or []),
            escalation_keywords=list(active.escalation_keywords or []),
            allowed_tools=DEFAULT_ALLOWED_TOOLS,
        )

    async def _run_model_turn(
        self,
        settings: Settings,
        conversation: Conversation,
        customer_message: str,
        config: SupportAgentConfig,
        registry: SupportToolRegistry,
        knowledge_entries: list[KnowledgeEntry],
        turn: AgentTurn | None = None,
    ) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
        if (settings.ai_provider or "").lower() == "extern_agent":
            reply, ai_response, tool_calls = await CrmExternAgentAdapter().reply(
                settings=settings,
                conversation=conversation,
                customer_message=customer_message,
                config=config,
                registry=registry,
                knowledge_entries=knowledge_entries,
                is_stale=lambda: turn is not None and not crm_agent_channel.is_latest(turn),
            )
            if not reply and ai_response.get("status") != "superseded":
                reply = self._fallback_reply(settings, customer_message, knowledge_entries, tool_calls)
            return reply, ai_response, tool_calls

        provider = OpenAIProvider(
            api_key=settings.ai_api_key or None,
            model=settings.ai_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )
        messages = self._compile_messages(settings, conversation, config, knowledge_entries)
        tools = registry.openai_tools(config.allowed_tools)
        all_tool_calls: list[dict[str, Any]] = []

        ai_response = await provider.chat(messages, tools=tools)
        if ai_response.get("status") != "ok":
            return (
                self._fallback_reply(settings, customer_message, knowledge_entries, all_tool_calls),
                ai_response,
                all_tool_calls,
            )

        for _ in range(5):
            if turn is not None and not crm_agent_channel.is_latest(turn):
                return "", {"status": "superseded", "usage": {}, "toolCalls": []}, all_tool_calls
            tool_calls = ai_response.get("toolCalls") or []
            if not tool_calls:
                break
            messages.append(
                {
                    "role": "assistant",
                    "content": ai_response.get("content") or "",
                    "tool_calls": tool_calls,
                }
            )
            for tool_call in tool_calls:
                if turn is not None and not crm_agent_channel.is_latest(turn):
                    return "", {"status": "superseded", "usage": {}, "toolCalls": []}, all_tool_calls
                tool_name = ((tool_call or {}).get("function") or {}).get("name", "")
                arguments = parse_tool_arguments(((tool_call or {}).get("function") or {}).get("arguments"))
                result = await registry.execute(tool_name, arguments, config.allowed_tools)
                all_tool_calls.append(
                    {
                        "name": tool_name,
                        "arguments": arguments,
                        "result": result,
                        "status": "success" if result.get("success") else "error",
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.get("id"),
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
            ai_response = await provider.chat(messages, tools=tools)
            if ai_response.get("status") != "ok":
                break

        reply = str(ai_response.get("content") or "").strip()
        if not reply:
            reply = self._fallback_reply(settings, customer_message, knowledge_entries, all_tool_calls)
        return reply, ai_response, all_tool_calls

    async def _run_heuristic_tools(
        self,
        registry: SupportToolRegistry,
        customer_message: str,
        intent: str,
        allowed_tools: list[str],
    ) -> list[dict[str, Any]]:
        lowered = customer_message.lower()
        should_create_ticket = (
            "create ticket" in lowered
            or "open ticket" in lowered
            or ("ticket" in lowered and intent in {"technical_support", "billing"})
        )
        if not should_create_ticket or "create_ticket" not in allowed_tools:
            return []

        priority = "urgent" if any(term in lowered for term in ["urgent", "critical", "immediately"]) else "medium"
        args = {
            "title": self._ticket_title(customer_message),
            "description": customer_message,
            "priority": priority,
            "department": "Support",
        }
        result = await registry.execute("create_ticket", args, allowed_tools)
        return [
            {
                "name": "create_ticket",
                "arguments": args,
                "result": result,
                "status": "success" if result.get("success") else "error",
            }
        ]

    def _compile_messages(
        self,
        settings: Settings,
        conversation: Conversation,
        config: SupportAgentConfig,
        knowledge_entries: list[KnowledgeEntry],
    ) -> list[dict[str, Any]]:
        knowledge_text = "\n\n".join(
            f"{entry.title}\n{entry.content[:1200]}" for entry in knowledge_entries
        )
        system_parts = [
            f"You are the AI customer support assistant for {settings.business_name}.",
            f"Business description: {settings.business_desc or 'Not provided.'}",
            f"Tone: {config.tone or settings.tone}. Reply style: {config.reply_style}.",
            f"Language: {settings.language}. Sales focus enabled: {config.sales_focus}.",
            "Use tools only when they directly help resolve the support case.",
            "Do not approve refunds, legal claims, discounts, or binding commitments.",
            "Escalate sensitive, legal, refund, or low-confidence cases to a human.",
        ]
        if knowledge_text:
            system_parts.append(f"Knowledge base:\n{knowledge_text}")

        messages: list[dict[str, Any]] = [{"role": "system", "content": "\n".join(system_parts)}]
        sorted_messages = sorted(conversation.messages, key=lambda item: item.created_at or "")
        for item in sorted_messages[-12:]:
            role = item.role
            if role == "customer":
                role = "user"
            elif role == "admin":
                role = "assistant"
            messages.append({"role": role, "content": item.content})
        return messages

    def _fallback_reply(
        self,
        settings: Settings,
        customer_message: str,
        knowledge_entries: list[KnowledgeEntry],
        tool_calls: list[dict[str, Any]],
    ) -> str:
        if tool_calls:
            ticket_call = next((call for call in tool_calls if call["name"] == "create_ticket"), None)
            if ticket_call and ticket_call["result"].get("success"):
                return (
                    "Thanks for the details. I created a support ticket for this issue, "
                    "and our team will review it shortly."
                )
        if knowledge_entries:
            entry = knowledge_entries[0]
            return (
                f"Thanks for reaching out. Based on our current guidance, {entry.title}: "
                f"{entry.content[:500]}"
            )
        return (
            f"Thanks for contacting {settings.business_name}. "
            "AI is not fully configured yet, but your message has been recorded for the team."
        )

    def _handoff_reply(self, settings: Settings, reason: str) -> str:
        return (
            f"Thanks for sharing this with {settings.business_name}. "
            "This needs a team member to review before we make any commitments. "
            f"I have escalated the conversation. Reason: {reason}."
        )

    def _sources_from_entries(self, entries: list[KnowledgeEntry]) -> list[dict[str, Any]]:
        return [
            {
                "id": entry.id,
                "title": entry.title,
                "contentPreview": entry.content[:200],
            }
            for entry in entries[:5]
        ]

    async def _load_conversation(self, conversation_id: str) -> Conversation | None:
        return await self.session.scalar(
            select(Conversation)
            .options(selectinload(Conversation.customer), selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )

    async def _load_knowledge_entries(self, knowledge_entry_ids: list[str]) -> list[KnowledgeEntry]:
        stmt = select(KnowledgeEntry).where(KnowledgeEntry.is_active.is_(True))
        if knowledge_entry_ids:
            stmt = stmt.where(KnowledgeEntry.id.in_(knowledge_entry_ids))
        stmt = stmt.order_by(KnowledgeEntry.priority.desc(), KnowledgeEntry.updated_at.desc()).limit(5)
        return list((await self.session.scalars(stmt)).all())

    async def _evaluate_automations(self, conversation: Conversation, customer_message: str) -> list[str]:
        service = AutomationService(AutomationRuleRepository(self.session), SQLAlchemyUnitOfWork(self.session))
        matches = await service.evaluate_rules(
            {
                "content": customer_message,
                "channel": conversation.channel,
                "customerName": conversation.customer_name,
            },
            {
                "id": conversation.id,
                "channel": conversation.channel,
                "customerName": conversation.customer_name,
            },
        )
        return [str(match.get("ruleName") or "") for match in matches]

    def _ticket_title(self, customer_message: str) -> str:
        title = customer_message.strip().replace("\n", " ")
        if len(title) > 80:
            title = title[:77] + "..."
        return title or "Support request"


def build_conversation_service(session: AsyncSession) -> ConversationService:
    return ConversationService(
        conversation_repo=ConversationRepository(session),
        message_repo=MessageRepository(session),
        customer_repo=CustomerRepository(session),
        uow=SQLAlchemyUnitOfWork(session),
    )


async def create_customer_message(
    session: AsyncSession,
    conversation_id: str,
    content: str,
) -> Any:
    service = build_conversation_service(session)
    return await service.create_message(conversation_id, MessageCreate(role="customer", content=content))

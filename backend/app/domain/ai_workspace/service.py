import json
import smtplib
from asyncio import Lock
from datetime import UTC, datetime
from email.message import EmailMessage

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.activity.schemas import ActivityLogCreate
from app.domain.activity.service import ActivityService
from app.core.database import create_schema
from app.domain.customer_support.service import CustomerSupportAgentService
from app.domain.tokens.service import TokenService
from app.infrastructure.db.models.conversations import Conversation, Customer
from app.infrastructure.db.models.knowledge import KnowledgeEntry
from app.infrastructure.db.models.operations import (
    AiAutoReplyLog,
    AiCustomerServiceConfig,
    AiIntentAnalysis,
    AiOutreachDelivery,
    AiOutreachDraft,
)
from app.infrastructure.db.models.operations import Settings
from app.infrastructure.integrations.ai import OpenAIProvider
from app.infrastructure.integrations.channels import (
    EmailChannelAdapter,
    PhoneChannelAdapter,
    WhatsAppChannelAdapter,
)

_schema_ensured = False
_schema_lock = Lock()


def _isoformat(value) -> str | None:
    return value.isoformat() if isinstance(value, datetime) else None


def _datetime_sort_key(item, field_name: str) -> float:
    value = getattr(item, field_name, None)
    return value.timestamp() if isinstance(value, datetime) else 0.0


class AIWorkspaceService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.activity_service = ActivityService(session)
        self.token_service = TokenService(session)

    async def _get_settings(self) -> Settings:
        settings = await self.session.get(Settings, "default")
        if not settings:
            settings = Settings()
            self.session.add(settings)
            await self.session.flush()
        return settings

    async def _ensure_workspace_schema(self) -> None:
        global _schema_ensured
        if _schema_ensured:
            return
        async with _schema_lock:
            if _schema_ensured:
                return
            await create_schema()
            _schema_ensured = True

    async def _get_customer(self, customer_id: str) -> Customer | None:
        return await self.session.scalar(
            select(Customer)
            .options(
                selectinload(Customer.conversations).selectinload(Conversation.messages),
                selectinload(Customer.notes),
            )
            .where(Customer.id == customer_id)
        )

    async def _get_knowledge_entries(self, knowledge_entry_ids: list[str]) -> list[KnowledgeEntry]:
        if not knowledge_entry_ids:
            return list(
                (
                    await self.session.scalars(
                        select(KnowledgeEntry)
                        .where(KnowledgeEntry.is_active.is_(True))
                        .order_by(KnowledgeEntry.priority.desc(), KnowledgeEntry.updated_at.desc())
                        .limit(5)
                    )
                ).all()
            )
        return list(
            (
                await self.session.scalars(
                    select(KnowledgeEntry)
                    .where(
                        KnowledgeEntry.is_active.is_(True),
                        KnowledgeEntry.id.in_(knowledge_entry_ids),
                    )
                    .order_by(KnowledgeEntry.priority.desc(), KnowledgeEntry.updated_at.desc())
                )
            ).all()
        )

    def _provider(self, settings: Settings) -> OpenAIProvider:
        return OpenAIProvider(
            api_key=settings.ai_api_key or None,
            model=settings.ai_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )

    def _usage_numbers(self, usage: dict | None, prompt_text: str, output_text: str) -> tuple[int, int, int]:
        prompt = int((usage or {}).get("prompt_tokens") or 0)
        completion = int((usage or {}).get("completion_tokens") or 0)
        total = int((usage or {}).get("total_tokens") or 0)
        if total <= 0:
            total = self.token_service.estimate_tokens(prompt_text, output_text)
            prompt = max(prompt, total // 2)
            completion = max(completion, total - prompt)
        return prompt, completion, total

    def _customer_context(self, customer: Customer) -> dict[str, object]:
        conversations = sorted(
            customer.conversations,
            key=lambda item: _datetime_sort_key(item, "updated_at"),
            reverse=True,
        )
        recent_messages: list[dict[str, str]] = []
        for conversation in conversations[:3]:
            ordered_messages = sorted(
                conversation.messages,
                key=lambda item: _datetime_sort_key(item, "created_at"),
                reverse=True,
            )
            for message in ordered_messages[:4]:
                recent_messages.append(
                    {
                        "conversationId": conversation.id,
                        "channel": conversation.channel,
                        "role": message.role,
                        "content": message.content,
                    }
                )
        return {
            "name": customer.name,
            "email": customer.email,
            "phone": customer.phone,
            "whatsapp": customer.whatsapp,
            "tags": customer.tags,
            "notes": [note.content for note in customer.notes[:5]],
            "recentMessages": recent_messages[:10],
        }

    async def generate_outreach(
        self,
        customer_id: str,
        knowledge_entry_ids: list[str],
        channel: str,
        purpose: str,
        language: str,
        auto_delivery_enabled: bool,
        auth_context,
    ) -> dict[str, object]:
        await self._ensure_workspace_schema()
        settings = await self._get_settings()
        customer = await self._get_customer(customer_id)
        if not customer:
            return {"error": "Customer not found"}

        entries = await self._get_knowledge_entries(knowledge_entry_ids)
        knowledge_text = "\n\n".join(f"{entry.title}\n{entry.content}" for entry in entries)
        customer_context = self._customer_context(customer)
        prompt = (
            f"Business: {settings.business_name}\n"
            f"Business description: {settings.business_desc}\n"
            f"Preferred tone: {settings.tone}\n"
            f"Target channel: {channel}\n"
            f"Outreach purpose: {purpose or 'General business development'}\n"
            f"Write language: {language or '简体中文'}\n"
            f"Customer profile: {json.dumps(customer_context, ensure_ascii=False)}\n"
            f"Knowledge:\n{knowledge_text}\n\n"
            "Generate a professional outbound development letter for this customer. "
            "Return JSON with subject, content, highlights, suggestedChannel. "
            "The subject and content must be written fully in the requested language."
        )
        provider = self._provider(settings)
        ai_response = await provider.chat(
            [
                {
                    "role": "system",
                    "content": "You are a B2B sales and customer engagement assistant.",
                },
                {"role": "user", "content": prompt},
            ]
        )
        raw_content = str(ai_response.get("content") or "").strip()
        subject = f"{settings.business_name} x {customer.name}"
        content = raw_content
        highlights = [entry.title for entry in entries[:3]]
        if raw_content.startswith("{"):
            try:
                parsed = json.loads(raw_content)
                subject = str(parsed.get("subject") or subject)
                content = str(parsed.get("content") or content)
                parsed_highlights = parsed.get("highlights")
                if isinstance(parsed_highlights, list):
                    highlights = [str(item) for item in parsed_highlights[:5]]
                channel = str(parsed.get("suggestedChannel") or channel)
            except json.JSONDecodeError:
                pass
        if not content:
            content = (
                f"Hello {customer.name},\n\n"
                f"We noticed opportunities where {settings.business_name} may support your business better. "
                f"Based on your profile and our available knowledge, we would love to share a few tailored ideas.\n\n"
                f"{knowledge_text[:900]}\n\nBest regards,\n{settings.business_name}"
            )

        prompt_tokens, completion_tokens, total_tokens = self._usage_numbers(ai_response.get("usage"), prompt, content)
        draft = AiOutreachDraft(
            customer_id=customer.id,
            knowledge_entry_ids=[entry.id for entry in entries],
            channel=channel,
            subject=subject,
            content=content,
            status="draft",
            auto_delivery_enabled=auto_delivery_enabled,
            usage_prompt_tokens=prompt_tokens,
            usage_completion_tokens=completion_tokens,
            usage_total_tokens=total_tokens,
            created_by_user_id=auth_context.user_id,
            created_by_name=auth_context.name,
        )
        self.session.add(draft)
        await self.token_service.record_consumption(
            total_tokens,
            "ai_outreach_generation",
            f"Generated outreach draft for {customer.name}",
            {
                "customerId": customer.id,
                "customerName": customer.name,
                "channel": channel,
            },
        )
        await self.activity_service.log_activity(
            ActivityLogCreate(
                action="ai_outreach_generated",
                entity="knowledge",
                entity_id=customer.id,
                description=f"{auth_context.name} generated an AI outreach draft for {customer.name}.",
                user_id=auth_context.user_id,
                user_name=auth_context.name,
                metadata={"customerId": customer.id, "channel": channel},
            )
        )
        await self.session.commit()
        await self.session.refresh(draft)
        return {
            "draftId": draft.id,
            "subject": draft.subject,
            "content": draft.content,
            "highlights": highlights,
            "channel": draft.channel,
            "autoDeliveryEnabled": draft.auto_delivery_enabled,
            "usage": {
                "promptTokens": prompt_tokens,
                "completionTokens": completion_tokens,
                "totalTokens": total_tokens,
            },
            "customer": {"id": customer.id, "name": customer.name},
        }

    async def send_outreach(
        self,
        draft_id: str,
        channel: str,
        subject: str,
        content: str,
        auto_delivery_enabled: bool,
        auth_context,
    ) -> dict[str, object]:
        await self._ensure_workspace_schema()
        draft = await self.session.get(AiOutreachDraft, draft_id)
        if not draft:
            return {"error": "Draft not found"}
        customer = await self._get_customer(draft.customer_id)
        if not customer:
            return {"error": "Customer not found"}

        settings = await self._get_settings()
        recipient = customer.email or customer.whatsapp or customer.phone
        status = "sent"
        error_message = ""

        if channel == "email":
            status, error_message = await self._send_email(settings, customer.email, subject, content)
        elif channel == "whatsapp":
            adapter = WhatsAppChannelAdapter()
            adapter_result = await adapter.send({"to": customer.whatsapp, "content": content, "subject": subject})
            status = str(adapter_result.get("status") or "queued")
        else:
            adapter = PhoneChannelAdapter()
            adapter_result = await adapter.send({"to": customer.phone, "content": content, "subject": subject})
            status = str(adapter_result.get("status") or "queued")

        delivery = AiOutreachDelivery(
            draft_id=draft.id,
            customer_id=customer.id,
            channel=channel,
            recipient=recipient or "",
            subject=subject,
            content=content,
            status=status,
            error_message=error_message,
            created_by_name=auth_context.name,
            sent_at=datetime.now(UTC) if status in {"sent", "queued"} else None,
        )
        self.session.add(delivery)

        draft.channel = channel
        draft.subject = subject
        draft.content = content
        draft.auto_delivery_enabled = auto_delivery_enabled
        draft.status = "auto_sent" if auto_delivery_enabled and status in {"sent", "queued"} else status

        await self.activity_service.log_activity(
            ActivityLogCreate(
                action="ai_outreach_sent",
                entity="knowledge",
                entity_id=delivery.id,
                description=f"{auth_context.name} sent an AI outreach message to {customer.name} via {channel}.",
                user_id=auth_context.user_id,
                user_name=auth_context.name,
                metadata={"customerId": customer.id, "channel": channel, "status": status},
            )
        )
        await self.session.commit()
        await self.session.refresh(delivery)
        return {
            "deliveryId": delivery.id,
            "status": delivery.status,
            "errorMessage": delivery.error_message,
            "recipient": delivery.recipient,
        }

    async def analyze_intent(
        self,
        customer_id: str,
        communication_goal: str,
        knowledge_entry_ids: list[str],
        auth_context,
    ) -> dict[str, object]:
        await self._ensure_workspace_schema()
        settings = await self._get_settings()
        customer = await self._get_customer(customer_id)
        if not customer:
            return {"error": "Customer not found"}

        entries = await self._get_knowledge_entries(knowledge_entry_ids)
        customer_context = self._customer_context(customer)
        prompt = (
            f"Analyze this customer for a sales/customer-success touchpoint.\n"
            f"Business: {settings.business_name}\n"
            f"Goal: {communication_goal}\n"
            f"Customer context: {json.dumps(customer_context, ensure_ascii=False)}\n"
            f"Knowledge: {json.dumps([{'title': entry.title, 'content': entry.content} for entry in entries], ensure_ascii=False)}\n"
            "Return JSON with keys: intent, customerQuality, successProbability, reasoning, replySuggestion, nextActions, riskFlags."
        )
        provider = self._provider(settings)
        ai_response = await provider.chat(
            [
                {
                    "role": "system",
                    "content": "You are an account strategist who evaluates intent, lead quality, and next-step recommendations.",
                },
                {"role": "user", "content": prompt},
            ]
        )
        raw_content = str(ai_response.get("content") or "").strip()
        result = {
            "intent": "Needs discovery",
            "customerQuality": "Medium",
            "successProbability": 0.55,
            "reasoning": raw_content or "The customer has enough context to continue engagement, but needs tailored follow-up.",
            "replySuggestion": raw_content or "Share a concise value-based reply and ask one clear qualifying question.",
            "nextActions": [
                "Send a tailored response aligned with the current goal.",
                "Follow up with product or company proof points.",
                "Review customer reactions and plan the next touchpoint.",
            ],
            "riskFlags": [],
        }
        if raw_content.startswith("{"):
            try:
                parsed = json.loads(raw_content)
                if isinstance(parsed, dict):
                    result.update(parsed)
            except json.JSONDecodeError:
                pass

        probability = float(result.get("successProbability") or 0.0)
        prompt_tokens, completion_tokens, total_tokens = self._usage_numbers(ai_response.get("usage"), prompt, raw_content)
        analysis = AiIntentAnalysis(
            customer_id=customer.id,
            communication_goal=communication_goal,
            knowledge_entry_ids=[entry.id for entry in entries],
            result_json=result,
            success_probability=probability,
            created_by_user_id=auth_context.user_id,
            created_by_name=auth_context.name,
        )
        self.session.add(analysis)
        await self.token_service.record_consumption(
            total_tokens,
            "ai_intent_analysis",
            f"Analyzed intent for {customer.name}",
            {"customerId": customer.id, "goal": communication_goal},
        )
        await self.activity_service.log_activity(
            ActivityLogCreate(
                action="ai_intent_analyzed",
                entity="customer",
                entity_id=customer.id,
                description=f"{auth_context.name} ran AI intent analysis for {customer.name}.",
                user_id=auth_context.user_id,
                user_name=auth_context.name,
                metadata={"customerId": customer.id, "goal": communication_goal},
            )
        )
        await self.session.commit()
        await self.session.refresh(analysis)
        return {"analysisId": analysis.id, "result": result}

    async def get_customer_service_config(self, customer_id: str | None = None) -> dict[str, object]:
        await self._ensure_workspace_schema()
        global_config = await self.session.scalar(
            select(AiCustomerServiceConfig)
            .where(AiCustomerServiceConfig.scope == "global")
            .order_by(AiCustomerServiceConfig.updated_at.desc(), AiCustomerServiceConfig.created_at.desc())
        )
        if not global_config:
            global_config = AiCustomerServiceConfig(scope="global", enabled=False)
            self.session.add(global_config)
            await self.session.commit()
            await self.session.refresh(global_config)

        customer_config = None
        if customer_id:
            customer_config = await self.session.scalar(
                select(AiCustomerServiceConfig)
                .where(
                    AiCustomerServiceConfig.scope == "customer",
                    AiCustomerServiceConfig.customer_id == customer_id,
                )
                .order_by(AiCustomerServiceConfig.updated_at.desc(), AiCustomerServiceConfig.created_at.desc())
            )
        return {
            "global": self._serialize_config(global_config),
            "customer": self._serialize_config(customer_config) if customer_config else None,
        }

    def _serialize_config(self, config: AiCustomerServiceConfig | None) -> dict[str, object]:
        if not config:
            return {}
        return {
            "id": config.id,
            "scope": config.scope,
            "customerId": config.customer_id,
            "enabled": config.enabled,
            "tone": config.tone,
            "salesFocus": config.sales_focus,
            "knowledgeEntryIds": config.knowledge_entry_ids or [],
            "escalationKeywords": config.escalation_keywords or [],
            "replyStyle": config.reply_style,
            "createdByName": config.created_by_name,
            "createdAt": _isoformat(config.created_at),
            "updatedAt": _isoformat(config.updated_at),
        }

    async def upsert_customer_service_config(self, payload: dict, auth_context) -> dict[str, object]:
        await self._ensure_workspace_schema()
        scope = str(payload.get("scope") or "global")
        customer_id = payload.get("customerId")
        enabled = bool(payload.get("enabled", False))

        if scope == "global" and enabled:
            enabled_customer_config = await self.session.scalar(
                select(AiCustomerServiceConfig).where(
                    AiCustomerServiceConfig.scope == "customer",
                    AiCustomerServiceConfig.enabled.is_(True),
                )
            )
            if enabled_customer_config:
                return {
                    "error": "已有单客户 AI 自动客服开启，请先关闭单客户配置后再开启全局开关。",
                }

        if scope == "customer" and enabled:
            global_config = await self.session.scalar(
                select(AiCustomerServiceConfig).where(
                    AiCustomerServiceConfig.scope == "global",
                    AiCustomerServiceConfig.enabled.is_(True),
                )
            )
            if global_config:
                return {
                    "error": "全局 AI 自动客服已开启，请先关闭全局开关后再开启单客户配置。",
                }

        stmt = (
            select(AiCustomerServiceConfig)
            .where(AiCustomerServiceConfig.scope == scope)
            .order_by(AiCustomerServiceConfig.updated_at.desc(), AiCustomerServiceConfig.created_at.desc())
        )
        if scope == "customer" and customer_id:
            stmt = stmt.where(AiCustomerServiceConfig.customer_id == str(customer_id))
        config = await self.session.scalar(stmt)
        if not config:
            config = AiCustomerServiceConfig(scope=scope, customer_id=str(customer_id) if customer_id else None)
            self.session.add(config)

        config.enabled = enabled if "enabled" in payload else config.enabled
        config.tone = str(payload.get("tone") or config.tone)
        config.sales_focus = bool(payload.get("salesFocus", config.sales_focus))
        config.knowledge_entry_ids = list(payload.get("knowledgeEntryIds") or config.knowledge_entry_ids or [])
        config.escalation_keywords = list(
            payload.get("escalationKeywords")
            or config.escalation_keywords
            or ["refund", "complaint", "lawsuit", "price", "discount"]
        )
        config.reply_style = str(payload.get("replyStyle") or config.reply_style)
        config.created_by_user_id = auth_context.user_id
        config.created_by_name = auth_context.name

        await self.activity_service.log_activity(
            ActivityLogCreate(
                action="ai_auto_service_updated",
                entity="knowledge",
                entity_id=config.customer_id,
                description=f"{auth_context.name} updated AI auto customer service settings for {scope}.",
                user_id=auth_context.user_id,
                user_name=auth_context.name,
                metadata={"scope": scope, "customerId": config.customer_id, "enabled": config.enabled},
            )
        )
        await self.session.commit()
        await self.session.refresh(config)
        return self._serialize_config(config)

    async def list_customer_service_customers(self) -> list[dict[str, object]]:
        await self._ensure_workspace_schema()
        configs = list(
            (
                await self.session.scalars(
                    select(AiCustomerServiceConfig)
                    .where(
                        AiCustomerServiceConfig.scope == "customer",
                        AiCustomerServiceConfig.enabled.is_(True),
                    )
                    .order_by(AiCustomerServiceConfig.updated_at.desc(), AiCustomerServiceConfig.created_at.desc())
                )
            ).all()
        )
        if not configs:
            return []

        customer_ids = [config.customer_id for config in configs if config.customer_id]
        customers = list(
            (
                await self.session.scalars(
                    select(Customer).where(Customer.id.in_(customer_ids))
                )
            ).all()
        )
        customer_map = {customer.id: customer for customer in customers}
        return [
            {
                "configId": config.id,
                "customerId": config.customer_id,
                "enabled": config.enabled,
                "tone": config.tone,
                "replyStyle": config.reply_style,
                "salesFocus": config.sales_focus,
                "knowledgeEntryIds": config.knowledge_entry_ids or [],
                "updatedAt": _isoformat(config.updated_at),
                "customer": (
                    {
                        "id": customer_map[config.customer_id].id,
                        "name": customer_map[config.customer_id].name,
                        "email": customer_map[config.customer_id].email,
                        "phone": customer_map[config.customer_id].phone,
                        "whatsapp": customer_map[config.customer_id].whatsapp,
                        "tags": customer_map[config.customer_id].tags,
                    }
                    if config.customer_id in customer_map
                    else None
                ),
            }
            for config in configs
        ]

    async def list_auto_reply_logs(self, customer_id: str | None = None) -> list[dict[str, object]]:
        await self._ensure_workspace_schema()
        stmt = select(AiAutoReplyLog).order_by(AiAutoReplyLog.created_at.desc()).limit(30)
        if customer_id:
            stmt = stmt.where(AiAutoReplyLog.customer_id == customer_id)
        rows = list((await self.session.scalars(stmt)).all())
        return [
            {
                "id": row.id,
                "conversationId": row.conversation_id,
                "customerId": row.customer_id,
                "configScope": row.config_scope,
                "customerMessage": row.customer_message,
                "aiReply": row.ai_reply,
                "status": row.status,
                "escalationReason": row.escalation_reason,
                "intent": row.intent,
                "sentiment": row.sentiment,
                "confidence": row.confidence,
                "toolCalls": row.tool_calls or [],
                "sources": row.sources or [],
                "agentStatus": row.agent_status,
                "usageTotalTokens": row.usage_total_tokens,
                "createdAt": _isoformat(row.created_at),
            }
            for row in rows
        ]

    async def maybe_auto_reply(
        self,
        conversation_id: str,
        customer_message: str,
    ) -> dict[str, object] | None:
        await self._ensure_workspace_schema()
        conversation = await self.session.scalar(
            select(Conversation)
            .options(selectinload(Conversation.customer), selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        if not conversation:
            return None

        agent_service = CustomerSupportAgentService(self.session)
        active_config = await agent_service.get_active_auto_reply_config(conversation)
        if not active_config:
            return None

        result = await agent_service.reply_to_conversation(
            conversation_id,
            customer_message,
            config=active_config,
            source="ai_auto_reply",
            write_auto_reply_log=True,
        )

        if result.status == "superseded":
            return None
        if result.status == "escalated":
            return {"status": "escalated", "reason": result.escalation_reason}
        return {
            "status": "sent",
            "message": result.assistant_message or {},
            "confidence": result.confidence,
            "intent": result.intent,
            "sentiment": result.sentiment,
        }

    async def _send_email(self, settings: Settings, to_email: str, subject: str, content: str) -> tuple[str, str]:
        if not to_email:
            return "failed", "Customer email is not configured."
        if not settings.smtp_host:
            adapter = EmailChannelAdapter()
            result = await adapter.send({"to": to_email, "subject": subject, "content": content})
            return str(result.get("status") or "queued"), ""

        message = EmailMessage()
        message["From"] = settings.smtp_from or settings.smtp_user
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(content)
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
                if settings.smtp_port == 587:
                    smtp.starttls()
                if settings.smtp_user:
                    smtp.login(settings.smtp_user, settings.smtp_pass)
                smtp.send_message(message)
            return "sent", ""
        except Exception as exc:
            return "failed", str(exc)

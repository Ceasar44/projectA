import uuid

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.infrastructure.db.base import Base


class Settings(Base):
    __tablename__ = "settings"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default="default")
    business_name: Mapped[str] = mapped_column(String(500), default="My Business")
    business_desc: Mapped[str] = mapped_column(String(5000), default="")
    welcome_message: Mapped[str] = mapped_column(String(2000), default="Hello! How can I help you today?")
    tone: Mapped[str] = mapped_column(String(50), default="friendly")
    language: Mapped[str] = mapped_column(String(20), default="auto")
    ai_provider: Mapped[str] = mapped_column(String(50), default="openai")
    ai_model: Mapped[str] = mapped_column(String(100), default="gpt-4o-mini")
    ai_api_key: Mapped[str] = mapped_column(String(500), default="")
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    smtp_host: Mapped[str] = mapped_column(String(500), default="")
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    smtp_user: Mapped[str] = mapped_column(String(300), default="")
    smtp_pass: Mapped[str] = mapped_column(String(500), default="")
    smtp_from: Mapped[str] = mapped_column(String(300), default="")
    imap_host: Mapped[str] = mapped_column(String(500), default="")
    imap_port: Mapped[int] = mapped_column(Integer, default=993)
    imap_user: Mapped[str] = mapped_column(String(300), default="")
    imap_pass: Mapped[str] = mapped_column(String(500), default="")
    twilio_sid: Mapped[str] = mapped_column(String(200), default="")
    twilio_token: Mapped[str] = mapped_column(String(200), default="")
    twilio_phone: Mapped[str] = mapped_column(String(50), default="")
    eleven_labs_key: Mapped[str] = mapped_column(String(200), default="")
    eleven_labs_voice: Mapped[str] = mapped_column(String(200), default="")
    whatsapp_mode: Mapped[str] = mapped_column(String(50), default="web")
    whatsapp_api_key: Mapped[str] = mapped_column(String(500), default="")
    whatsapp_phone: Mapped[str] = mapped_column(String(50), default="")
    telegram_bot_token: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Channel(Base):
    __tablename__ = "channel"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    type: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="disconnected")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CallLog(Base):
    __tablename__ = "call_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    call_sid: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    from_number: Mapped[str] = mapped_column("from", String(100), default="")
    to_number: Mapped[str] = mapped_column("to", String(100), default="")
    duration: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="initiated")
    recording: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AutomationRule(Base):
    __tablename__ = "automation_rule"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000), default="")
    type: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    conditions: Mapped[list] = mapped_column(JSON, default=list)
    actions: Mapped[list] = mapped_column(JSON, default=list)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BusinessHours(Base):
    __tablename__ = "business_hours"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default="default")
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    timezone: Mapped[str] = mapped_column(String(100), default="UTC")
    monday: Mapped[str] = mapped_column(String(50), default="09:00-18:00")
    tuesday: Mapped[str] = mapped_column(String(50), default="09:00-18:00")
    wednesday: Mapped[str] = mapped_column(String(50), default="09:00-18:00")
    thursday: Mapped[str] = mapped_column(String(50), default="09:00-18:00")
    friday: Mapped[str] = mapped_column(String(50), default="09:00-18:00")
    saturday: Mapped[str] = mapped_column(String(50), default="")
    sunday: Mapped[str] = mapped_column(String(50), default="")
    offline_message: Mapped[str] = mapped_column(
        String(500), default="We are currently offline. We will get back to you during business hours."
    )


class SLARule(Base):
    __tablename__ = "sla_rule"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000), default="")
    channel: Mapped[str] = mapped_column(String(50), default="all")
    priority: Mapped[str] = mapped_column(String(50), default="all")
    first_response_mins: Mapped[int] = mapped_column(Integer, default=30)
    resolution_mins: Mapped[int] = mapped_column(Integer, default=480)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class CannedResponse(Base):
    __tablename__ = "canned_response"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), default="General")
    shortcut: Mapped[str] = mapped_column(String(50), default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Webhook(Base):
    __tablename__ = "webhook"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000), default="")
    url: Mapped[str] = mapped_column(String(2000))
    method: Mapped[str] = mapped_column(String(10), default="POST")
    headers: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    trigger_on: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class WebhookDelivery(Base):
    __tablename__ = "webhook_delivery"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    webhook_id: Mapped[str] = mapped_column(ForeignKey("webhook.id", ondelete="CASCADE"), index=True)
    event: Mapped[str] = mapped_column(String(200))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_retry_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action: Mapped[str] = mapped_column(String(200), index=True)
    entity: Mapped[str] = mapped_column(String(100), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    user_name: Mapped[str] = mapped_column(String(200), default="System")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TokenWallet(Base):
    __tablename__ = "token_wallet"

    id: Mapped[str] = mapped_column(String(50), primary_key=True, default="default")
    balance_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_consumed_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_recharged_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TokenRechargeOrder(Base):
    __tablename__ = "token_recharge_order"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_name: Mapped[str] = mapped_column(String(200), default="")
    payment_method: Mapped[str] = mapped_column(String(50), default="alipay", index=True)
    amount_cents: Mapped[int] = mapped_column(Integer, default=0)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_by_name: Mapped[str] = mapped_column(String(200), default="System")
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TokenLedgerEntry(Base):
    __tablename__ = "token_ledger_entry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kind: Mapped[str] = mapped_column(String(50), index=True)
    source: Mapped[str] = mapped_column(String(100), index=True)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    balance_after: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(String(500), default="")
    reference_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class AiOutreachDraft(Base):
    __tablename__ = "ai_outreach_draft"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id: Mapped[str] = mapped_column(ForeignKey("customer.id", ondelete="CASCADE"), index=True)
    knowledge_entry_ids: Mapped[list] = mapped_column(JSON, default=list)
    channel: Mapped[str] = mapped_column(String(50), default="email")
    subject: Mapped[str] = mapped_column(String(500), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="draft", index=True)
    auto_delivery_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    usage_prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    usage_completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    usage_total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_by_name: Mapped[str] = mapped_column(String(200), default="System")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AiOutreachDelivery(Base):
    __tablename__ = "ai_outreach_delivery"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    draft_id: Mapped[str | None] = mapped_column(ForeignKey("ai_outreach_draft.id", ondelete="SET NULL"), nullable=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customer.id", ondelete="CASCADE"), index=True)
    channel: Mapped[str] = mapped_column(String(50), default="email")
    recipient: Mapped[str] = mapped_column(String(500), default="")
    subject: Mapped[str] = mapped_column(String(500), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="queued", index=True)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_by_name: Mapped[str] = mapped_column(String(200), default="System")
    sent_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AiIntentAnalysis(Base):
    __tablename__ = "ai_intent_analysis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id: Mapped[str] = mapped_column(ForeignKey("customer.id", ondelete="CASCADE"), index=True)
    communication_goal: Mapped[str] = mapped_column(Text, default="")
    knowledge_entry_ids: Mapped[list] = mapped_column(JSON, default=list)
    result_json: Mapped[dict] = mapped_column("result", JSON, default=dict)
    success_probability: Mapped[float] = mapped_column(Float, default=0.0)
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_by_name: Mapped[str] = mapped_column(String(200), default="System")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class AiCustomerServiceConfig(Base):
    __tablename__ = "ai_customer_service_config"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scope: Mapped[str] = mapped_column(String(50), default="global", index=True)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customer.id", ondelete="CASCADE"), nullable=True, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    tone: Mapped[str] = mapped_column(String(50), default="friendly")
    sales_focus: Mapped[bool] = mapped_column(Boolean, default=True)
    knowledge_entry_ids: Mapped[list] = mapped_column(JSON, default=list)
    escalation_keywords: Mapped[list] = mapped_column(JSON, default=list)
    reply_style: Mapped[str] = mapped_column(String(100), default="helpful and concise")
    created_by_user_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    created_by_name: Mapped[str] = mapped_column(String(200), default="System")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AiAutoReplyLog(Base):
    __tablename__ = "ai_auto_reply_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversation.id", ondelete="CASCADE"), index=True)
    customer_id: Mapped[str | None] = mapped_column(ForeignKey("customer.id", ondelete="SET NULL"), nullable=True, index=True)
    config_scope: Mapped[str] = mapped_column(String(50), default="global")
    knowledge_entry_ids: Mapped[list] = mapped_column(JSON, default=list)
    customer_message: Mapped[str] = mapped_column(Text, default="")
    ai_reply: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="sent", index=True)
    escalation_reason: Mapped[str] = mapped_column(String(500), default="")
    usage_prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    usage_completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    usage_total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    intent: Mapped[str] = mapped_column(String(100), default="")
    sentiment: Mapped[str] = mapped_column(String(50), default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    tool_calls: Mapped[list] = mapped_column(JSON, default=list)
    sources: Mapped[list] = mapped_column(JSON, default=list)
    agent_status: Mapped[str] = mapped_column(String(50), default="")
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class Campaign(Base):
    __tablename__ = "campaign"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000), default="")
    channel: Mapped[str] = mapped_column(String(50), default="email")
    message: Mapped[str] = mapped_column(Text)
    subject: Mapped[str] = mapped_column(String(500), default="")
    segments: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(50), default="draft")
    scheduled_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Flow(Base):
    __tablename__ = "flow"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(String(1000), default="")
    start_node_id: Mapped[str] = mapped_column(String(100), default="")
    nodes: Mapped[list] = mapped_column(JSON, default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

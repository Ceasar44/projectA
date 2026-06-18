from dataclasses import dataclass, field
from typing import Any


@dataclass
class SupportAgentConfig:
    config_scope: str = "chat"
    tone: str = "friendly"
    reply_style: str = "helpful and concise"
    sales_focus: bool = True
    knowledge_entry_ids: list[str] = field(default_factory=list)
    escalation_keywords: list[str] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)


@dataclass
class SupportAgentResult:
    conversation_id: str
    reply: str
    status: str
    confidence: float
    intent: str
    sentiment: str
    escalation_reason: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    provider_status: str = ""
    usage: dict[str, Any] = field(default_factory=dict)
    assistant_message: dict[str, Any] | None = None
    automation_matches: list[str] = field(default_factory=list)

    def to_api_response(self) -> dict[str, Any]:
        return {
            "conversationId": self.conversation_id,
            "response": self.reply,
            "status": self.status,
            "confidence": self.confidence,
            "intent": self.intent,
            "sentiment": self.sentiment,
            "escalationReason": self.escalation_reason,
            "toolCalls": self.tool_calls,
            "sources": self.sources,
        }

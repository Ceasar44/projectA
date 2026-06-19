from __future__ import annotations

from types import SimpleNamespace

from app.domain.customer_support.memory import CrmMemoryIdentity
from app.domain.customer_support.prompt_builder import (
    CustomerSupportPromptContext,
    build_customer_support_prompt,
)
from app.domain.customer_support.schemas import SupportAgentConfig


def test_extern_agent_prompt_is_sectioned_for_customer_support() -> None:
    settings = SimpleNamespace(
        business_name="Acme Desk",
        business_desc="Helps teams manage customer support.",
        tone="professional",
        language="auto",
        ai_model="gpt-test",
    )
    config = SupportAgentConfig(
        tone="warm",
        reply_style="brief and concrete",
        sales_focus=False,
        allowed_tools=["create_ticket"],
        escalation_keywords=["refund"],
    )
    context = CustomerSupportPromptContext(
        settings=settings,
        config=config,
        knowledge_entries=[
            SimpleNamespace(title="Refund policy", content="Refund requests require human review."),
        ],
        memory_identity=CrmMemoryIdentity(
            business_id="business-1",
            customer_id="customer-1",
            conversation_id="conversation-1",
        ),
        memory_snapshot={
            "customer": [{"kind": "preference", "content": "Prefers email follow-ups."}],
            "conversation": [{"kind": "issue", "content": "Reported a billing problem."}],
        },
        tools=[SimpleNamespace(name="create_ticket", description="Create a support ticket.")],
        runtime_info={
            "current_time": "2026-06-19T12:00:00+00:00",
            "model": "gpt-test",
            "channel": "email",
            "conversation_id": "conversation-1",
        },
    )

    prompt = build_customer_support_prompt(context)

    assert prompt.index("## Identity") < prompt.index("## Tooling")
    assert prompt.index("## Tooling") < prompt.index("## CRM memory")
    assert "You are the AI customer support assistant for Acme Desk." in prompt
    assert "- Tone: warm" in prompt
    assert "- Sales focus: disabled" in prompt
    assert "- Escalation keywords configured for this agent: refund." in prompt
    assert "- create_ticket: Create a support ticket." in prompt
    assert (
        "Memory identity: business=business-1, customer=customer-1, conversation=conversation-1."
        in prompt
    )
    assert "- [preference] Prefers email follow-ups." in prompt
    assert "### Refund policy\nRefund requests require human review." in prompt
    assert "Answer with the final customer-facing reply only." in prompt


def test_extern_agent_prompt_handles_missing_optional_context() -> None:
    settings = SimpleNamespace(
        business_name="Acme Desk",
        business_desc="",
        tone="friendly",
        language="en",
        ai_model="gpt-test",
    )
    config = SupportAgentConfig(allowed_tools=[])

    prompt = build_customer_support_prompt(
        CustomerSupportPromptContext(settings=settings, config=config)
    )

    assert "Business description: Not provided." in prompt
    assert "- No CRM business tools are enabled for this turn." in prompt
    assert "No approved knowledge entries were attached to this turn." in prompt
    assert "Memory tools are available for approved CRM memory only." in prompt

from __future__ import annotations

import asyncio
import json
import sys
import types
from pathlib import Path
from threading import RLock
from typing import Any

from app.core.logging import get_logger
from app.domain.customer_support.schemas import SupportAgentConfig
from app.infrastructure.db.models.conversations import Conversation
from app.infrastructure.db.models.knowledge import KnowledgeEntry
from app.infrastructure.db.models.operations import Settings
from app.infrastructure.integrations.ai import OpenAIProvider

logger = get_logger(__name__)


class _SafeSrcLogger:
    def _log(self, level: str, message: Any, *args, **kwargs) -> None:
        return None

    def debug(self, message: Any, *args, **kwargs) -> None:
        self._log("debug", message, *args, **kwargs)

    def info(self, message: Any, *args, **kwargs) -> None:
        self._log("info", message, *args, **kwargs)

    def warning(self, message: Any, *args, **kwargs) -> None:
        self._log("warning", message, *args, **kwargs)

    def error(self, message: Any, *args, **kwargs) -> None:
        self._log("error", message, *args, **kwargs)

    def exception(self, message: Any, *args, **kwargs) -> None:
        self._log("error", message, *args, **kwargs)


def _ensure_src_runtime() -> None:
    """Make the legacy src/agent package importable inside the backend process."""
    project_root = Path(__file__).resolve().parents[4]
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    if "common.log" not in sys.modules:
        common_mod = sys.modules.setdefault("common", types.ModuleType("common"))
        log_mod = types.ModuleType("common.log")
        log_mod.logger = _SafeSrcLogger()
        sys.modules["common.log"] = log_mod
        setattr(common_mod, "log", log_mod)
    else:
        try:
            sys.modules["common.log"].logger = _SafeSrcLogger()
        except Exception:
            pass

    if "common.i18n" not in sys.modules:
        common_mod = sys.modules.setdefault("common", types.ModuleType("common"))
        i18n_mod = types.ModuleType("common.i18n")
        i18n_mod.t = lambda zh, en=None: en or zh
        i18n_mod.get_language = lambda: "en"
        sys.modules["common.i18n"] = i18n_mod
        setattr(common_mod, "i18n", i18n_mod)

    if "common.utils" not in sys.modules:
        common_mod = sys.modules.setdefault("common", types.ModuleType("common"))
        utils_mod = types.ModuleType("common.utils")
        utils_mod.expand_path = lambda value: str(Path(value).expanduser())
        utils_mod.is_cloud_deployment = lambda: False
        sys.modules["common.utils"] = utils_mod
        setattr(common_mod, "utils", utils_mod)

    common_mod = sys.modules.setdefault("common", types.ModuleType("common"))
    if not hasattr(common_mod, "const"):
        const_mod = types.ModuleType("common.const")
        sys.modules["common.const"] = const_mod
        setattr(common_mod, "const", const_mod)

    if "config" not in sys.modules:
        config_mod = types.ModuleType("config")
        runtime_config = {
            "agent_max_context_turns": 20,
            "agent_max_steps": 8,
            "agent_max_context_tokens": 50000,
            "enable_thinking": False,
            "debug": False,
            "conversation_persistence": False,
            "knowledge": False,
        }
        config_mod.conf = lambda: runtime_config
        sys.modules["config"] = config_mod


class BackendSrcAgentModel:
    """LLMModel-compatible adapter backed by the backend OpenAIProvider."""

    def __init__(self, settings: Settings):
        _ensure_src_runtime()
        self.model = settings.ai_model
        self.provider = OpenAIProvider(
            api_key=settings.ai_api_key or None,
            model=settings.ai_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )

    def call(self, request):
        response = self._run_provider(request)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("error") or response.get("content") or "src agent model call failed")
        return response

    def call_stream(self, request):
        response = self.call(request)
        content = response.get("content") or ""
        tool_calls = response.get("toolCalls") or []
        delta: dict[str, Any] = {}
        if content:
            delta["content"] = content
        if tool_calls:
            delta["tool_calls"] = [
                {
                    "index": idx,
                    "id": call.get("id"),
                    "function": {
                        "name": ((call.get("function") or {}).get("name") or ""),
                        "arguments": ((call.get("function") or {}).get("arguments") or "{}"),
                    },
                }
                for idx, call in enumerate(tool_calls)
            ]
        if delta:
            yield {"choices": [{"delta": delta, "finish_reason": None}]}
        yield {"choices": [{"delta": {}, "finish_reason": "stop"}]}

    def _run_provider(self, request) -> dict[str, Any]:
        messages = self._to_openai_messages(getattr(request, "messages", []) or [])
        system_prompt = getattr(request, "system", None)
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})
        tools = self._to_openai_tools(getattr(request, "tools", None))

        async def _call():
            return await self.provider.chat(messages, tools=tools)

        return asyncio.run(_call())

    @staticmethod
    def _text_from_blocks(content: Any) -> str:
        if isinstance(content, str):
            return content
        if not isinstance(content, list):
            return str(content or "")
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
        return "\n".join(part for part in parts if part)

    @classmethod
    def _to_openai_messages(cls, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        converted: list[dict[str, Any]] = []
        for message in messages:
            role = message.get("role")
            content = message.get("content")
            if role == "user" and isinstance(content, list) and any(
                isinstance(block, dict) and block.get("type") == "tool_result" for block in content
            ):
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_result":
                        continue
                    converted.append(
                        {
                            "role": "tool",
                            "tool_call_id": block.get("tool_use_id") or "",
                            "content": cls._text_from_blocks(block.get("content")),
                        }
                    )
                continue
            if role == "assistant" and isinstance(content, list):
                tool_calls = []
                for block in content:
                    if not isinstance(block, dict) or block.get("type") != "tool_use":
                        continue
                    tool_calls.append(
                        {
                            "id": block.get("id") or "",
                            "type": "function",
                            "function": {
                                "name": block.get("name") or "",
                                "arguments": json.dumps(block.get("input") or {}, ensure_ascii=False),
                            },
                        }
                    )
                item: dict[str, Any] = {"role": "assistant", "content": cls._text_from_blocks(content)}
                if tool_calls:
                    item["tool_calls"] = tool_calls
                converted.append(item)
                continue
            converted.append({"role": role, "content": cls._text_from_blocks(content)})
        return converted

    @staticmethod
    def _to_openai_tools(tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        if not tools:
            return None
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.get("name") or "",
                    "description": tool.get("description") or "",
                    "parameters": tool.get("input_schema") or {"type": "object", "properties": {}},
                },
            }
            for tool in tools
        ]


class SrcAgentAdapter:
    """Bridge backend customer-support context into src/agent without AgentBridge."""

    _lock = RLock()

    async def reply(
        self,
        *,
        settings: Settings,
        conversation: Conversation,
        customer_message: str,
        config: SupportAgentConfig,
        knowledge_entries: list[KnowledgeEntry],
    ) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
        return await asyncio.to_thread(
            self._reply_sync,
            settings,
            conversation,
            customer_message,
            config,
            knowledge_entries,
        )

    def _reply_sync(
        self,
        settings: Settings,
        conversation: Conversation,
        customer_message: str,
        config: SupportAgentConfig,
        knowledge_entries: list[KnowledgeEntry],
    ) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
        _ensure_src_runtime()
        from extern_agent.agent.protocol import Agent

        system_prompt = self._build_system_prompt(settings, config, knowledge_entries)
        agent = Agent(
            system_prompt=system_prompt,
            description="Backend customer support src agent",
            model=BackendSrcAgentModel(settings),
            tools=[],
            output_mode="logger",
            max_steps=8,
            enable_skills=False,
            workspace_dir=None,
            memory_manager=None,
        )
        agent.messages = self._history_messages(conversation, customer_message)

        events: list[dict[str, Any]] = []

        def _on_event(event: dict[str, Any]):
            events.append(event)

        try:
            reply = agent.run_stream(customer_message, on_event=_on_event)
        except Exception as exc:
            logger.warning("src agent reply failed: %s", str(exc))
            return (
                "",
                {"provider": "src_agent", "status": "error", "content": "", "error": str(exc)},
                [],
            )

        return (
            (reply or "").strip(),
            {
                "provider": "src_agent",
                "status": "ok",
                "content": (reply or "").strip(),
                "usage": {},
                "events": self._summarize_events(events),
            },
            [],
        )

    @staticmethod
    def _history_messages(conversation: Conversation, customer_message: str) -> list[dict[str, Any]]:
        rows = sorted(conversation.messages, key=lambda item: item.created_at or "")
        if rows and rows[-1].role == "customer" and rows[-1].content == customer_message:
            rows = rows[:-1]
        history = []
        for item in rows[-12:]:
            role = "user" if item.role == "customer" else "assistant"
            history.append({"role": role, "content": [{"type": "text", "text": item.content}]})
        return history

    @staticmethod
    def _build_system_prompt(
        settings: Settings,
        config: SupportAgentConfig,
        knowledge_entries: list[KnowledgeEntry],
    ) -> str:
        knowledge_text = "\n\n".join(
            f"{entry.title}\n{entry.content[:1200]}" for entry in knowledge_entries
        )
        parts = [
            f"You are the AI customer support assistant for {settings.business_name}.",
            f"Business description: {settings.business_desc or 'Not provided.'}",
            f"Tone: {config.tone or settings.tone}. Reply style: {config.reply_style}.",
            f"Language: {settings.language}. Sales focus enabled: {config.sales_focus}.",
            "Answer as a concise customer-support agent.",
            "Do not approve refunds, legal claims, discounts, or binding commitments.",
            "Escalate sensitive, legal, refund, or low-confidence cases to a human.",
        ]
        if knowledge_text:
            parts.append(f"Knowledge base:\n{knowledge_text}")
        return "\n".join(parts)

    @staticmethod
    def _summarize_events(events: list[dict[str, Any]]) -> dict[str, Any]:
        tool_events = [
            event.get("data", {})
            for event in events
            if event.get("type") in {"tool_execution_start", "tool_execution_end"}
        ]
        return {"eventCount": len(events), "toolEvents": tool_events}

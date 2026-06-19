from __future__ import annotations

import asyncio
import json
import sys
import types
from collections.abc import Callable
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING, Any

from app.infrastructure.db.models.conversations import Conversation
from app.infrastructure.db.models.knowledge import KnowledgeEntry
from app.infrastructure.db.models.operations import Settings
from app.infrastructure.integrations.ai import OpenAIProvider

if TYPE_CHECKING:
    from app.domain.customer_support.schemas import SupportAgentConfig
    from app.domain.customer_support.tools import SupportToolRegistry


class _SafeExternAgentLogger:
    def debug(self, message: Any, *args, **kwargs) -> None:
        return None

    def info(self, message: Any, *args, **kwargs) -> None:
        return None

    def warning(self, message: Any, *args, **kwargs) -> None:
        return None

    def error(self, message: Any, *args, **kwargs) -> None:
        return None

    def exception(self, message: Any, *args, **kwargs) -> None:
        return None


def _ensure_extern_agent_runtime() -> None:
    """Expose backend/extern_agent as the legacy top-level agent runtime."""
    backend_root = Path(__file__).resolve().parents[3]
    extern_agent_root = backend_root / "extern_agent"
    if str(extern_agent_root) not in sys.path:
        sys.path.insert(0, str(extern_agent_root))

    common_module = sys.modules.setdefault("common", types.ModuleType("common"))
    if not hasattr(common_module, "__path__"):
        common_module.__path__ = [str(extern_agent_root / "common")]

    log_module = sys.modules.get("common.log")
    if log_module is None:
        log_module = types.ModuleType("common.log")
        sys.modules["common.log"] = log_module
    log_module.logger = _SafeExternAgentLogger()
    setattr(common_module, "log", log_module)

    if "common.i18n" not in sys.modules:
        i18n_module = types.ModuleType("common.i18n")
        i18n_module.t = lambda zh, en=None: en or zh
        i18n_module.get_language = lambda: "en"
        sys.modules["common.i18n"] = i18n_module
        setattr(common_module, "i18n", i18n_module)

    if "config" not in sys.modules:
        runtime_config = {
            "agent_max_context_turns": 20,
            "agent_max_steps": 8,
            "agent_max_context_tokens": 50000,
            "conversation_persistence": False,
            "enable_thinking": False,
            "knowledge": False,
            "debug": False,
        }
        config_module = types.ModuleType("config")
        config_module.conf = lambda: runtime_config
        sys.modules["config"] = config_module


class CrmExternAgentModel:
    """extern_agent LLMModel adapter backed by the backend OpenAI provider."""

    def __init__(self, settings: Settings) -> None:
        _ensure_extern_agent_runtime()
        self.model = settings.ai_model
        self.provider = OpenAIProvider(
            api_key=settings.ai_api_key or None,
            model=settings.ai_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
        )

    def call(self, request: Any) -> dict[str, Any]:
        response = self._run_provider(request)
        if response.get("status") != "ok":
            raise RuntimeError(response.get("error") or response.get("content") or "extern agent model call failed")
        return response

    def call_stream(self, request: Any):
        response = self.call(request)
        content = str(response.get("content") or "")
        tool_calls = response.get("toolCalls") or []
        delta: dict[str, Any] = {}
        if content:
            delta["content"] = content
        if tool_calls:
            delta["tool_calls"] = [
                {
                    "index": index,
                    "id": tool_call.get("id"),
                    "function": {
                        "name": ((tool_call.get("function") or {}).get("name") or ""),
                        "arguments": ((tool_call.get("function") or {}).get("arguments") or "{}"),
                    },
                }
                for index, tool_call in enumerate(tool_calls)
            ]
        if delta:
            yield {"choices": [{"delta": delta, "finish_reason": None}]}
        yield {"choices": [{"delta": {}, "finish_reason": "stop"}]}

    def _run_provider(self, request: Any) -> dict[str, Any]:
        messages = self._to_openai_messages(getattr(request, "messages", []) or [])
        system_prompt = getattr(request, "system", None)
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})
        tools = self._to_openai_tools(getattr(request, "tools", None))

        async def _call_provider() -> dict[str, Any]:
            return await self.provider.chat(messages, tools=tools)

        return asyncio.run(_call_provider())

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
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        converted.append(
                            {
                                "role": "tool",
                                "tool_call_id": block.get("tool_use_id") or "",
                                "content": cls._text_from_blocks(block.get("content")),
                            }
                        )
                continue
            if role == "assistant" and isinstance(content, list):
                item: dict[str, Any] = {"role": "assistant", "content": cls._text_from_blocks(content)}
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
            elif block.get("type") == "tool_result":
                parts.append(CrmExternAgentModel._text_from_blocks(block.get("content")))
        return "\n".join(part for part in parts if part)


class CrmSupportTool:
    def __init__(
        self,
        *,
        name: str,
        description: str,
        params: dict[str, Any],
        registry: SupportToolRegistry,
        allowed_tools: list[str],
        loop: asyncio.AbstractEventLoop,
        is_stale: Callable[[], bool],
    ) -> None:
        _ensure_extern_agent_runtime()
        from agent.tools.base_tool import ToolStage

        self.name = name
        self.description = description
        self.params = params
        self.stage = ToolStage.PRE_PROCESS
        self.registry = registry
        self.allowed_tools = allowed_tools
        self.loop = loop
        self.is_stale = is_stale

    def get_json_schema(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "parameters": self.params}

    def execute_tool(self, params: dict[str, Any]):
        return self.execute(params)

    def execute(self, params: dict[str, Any]):
        from agent.tools.base_tool import ToolResult

        if self.is_stale():
            return ToolResult.fail({"success": False, "message": "This agent turn is stale."})
        future = asyncio.run_coroutine_threadsafe(
            self.registry.execute(self.name, params, self.allowed_tools),
            self.loop,
        )
        result = future.result()
        if self.is_stale():
            return ToolResult.fail({"success": False, "message": "This agent turn became stale."})
        return ToolResult.success(result) if result.get("success") else ToolResult.fail(result)


class CrmExternAgentAdapter:
    """Runs one disposable extern_agent instance for a CRM conversation turn."""

    async def reply(
        self,
        *,
        settings: Settings,
        conversation: Conversation,
        customer_message: str,
        config: SupportAgentConfig,
        registry: SupportToolRegistry,
        knowledge_entries: list[KnowledgeEntry],
        is_stale: Callable[[], bool],
    ) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
        loop = asyncio.get_running_loop()
        return await asyncio.to_thread(
            self._reply_sync,
            settings,
            conversation,
            customer_message,
            config,
            registry,
            knowledge_entries,
            loop,
            is_stale,
        )

    def _reply_sync(
        self,
        settings: Settings,
        conversation: Conversation,
        customer_message: str,
        config: SupportAgentConfig,
        registry: SupportToolRegistry,
        knowledge_entries: list[KnowledgeEntry],
        loop: asyncio.AbstractEventLoop,
        is_stale: Callable[[], bool],
    ) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
        _ensure_extern_agent_runtime()
        from agent.protocol import Agent

        if is_stale():
            return "", {"provider": "extern_agent", "status": "superseded", "usage": {}}, []

        tools = self._build_tools(registry, config.allowed_tools, loop, is_stale)
        system_prompt = self._build_system_prompt(settings, config, knowledge_entries)
        cancel_event = Event()
        agent = Agent(
            system_prompt=system_prompt,
            description="CRM customer-support agent",
            model=CrmExternAgentModel(settings),
            tools=tools,
            output_mode="logger",
            max_steps=8,
            enable_skills=False,
            workspace_dir=None,
            memory_manager=None,
        )
        agent.get_full_system_prompt = lambda skill_filter=None: system_prompt
        agent.messages = self._history_messages(conversation, customer_message)

        events: list[dict[str, Any]] = []

        def _on_event(event: dict[str, Any]) -> None:
            events.append(event)
            if is_stale():
                cancel_event.set()

        try:
            reply = agent.run_stream(customer_message, on_event=_on_event, clear_history=False, cancel_event=cancel_event)
        except Exception as exc:
            if is_stale():
                return "", {"provider": "extern_agent", "status": "superseded", "usage": {}}, []
            return "", {"provider": "extern_agent", "status": "error", "error": str(exc), "usage": {}}, []
        finally:
            for tool in tools:
                close = getattr(tool, "close", None)
                if callable(close):
                    close()
            agent.tools = []
            agent.messages = []

        if is_stale():
            return "", {"provider": "extern_agent", "status": "superseded", "usage": {}}, []

        return (
            str(reply or "").strip(),
            {
                "provider": "extern_agent",
                "status": "ok",
                "content": str(reply or "").strip(),
                "usage": getattr(agent, "last_usage", None) or {},
                "events": self._summarize_events(events),
            },
            self._tool_calls_from_events(events),
        )

    @staticmethod
    def _build_tools(
        registry: SupportToolRegistry,
        allowed_tools: list[str],
        loop: asyncio.AbstractEventLoop,
        is_stale: Callable[[], bool],
    ) -> list[CrmSupportTool]:
        return [
            CrmSupportTool(
                name=tool["function"]["name"],
                description=tool["function"].get("description") or "",
                params=tool["function"].get("parameters") or {"type": "object", "properties": {}},
                registry=registry,
                allowed_tools=allowed_tools,
                loop=loop,
                is_stale=is_stale,
            )
            for tool in registry.openai_tools(allowed_tools)
        ]

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
            "Use tools only when they directly help resolve the support case.",
            "Do not approve refunds, legal claims, discounts, or binding commitments.",
            "Escalate sensitive, legal, refund, or low-confidence cases to a human.",
            "Answer with the final customer-facing reply only.",
        ]
        if knowledge_text:
            parts.append(f"Knowledge base:\n{knowledge_text}")
        return "\n".join(parts)

    @staticmethod
    def _summarize_events(events: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "eventCount": len(events),
            "toolEventCount": sum(
                1 for event in events if event.get("type") in {"tool_execution_start", "tool_execution_end"}
            ),
        }

    @staticmethod
    def _tool_calls_from_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        starts: dict[str, dict[str, Any]] = {}
        calls: list[dict[str, Any]] = []
        for event in events:
            data = event.get("data") or {}
            if event.get("type") == "tool_execution_start":
                starts[str(data.get("tool_call_id") or "")] = data
            elif event.get("type") == "tool_execution_end":
                tool_call_id = str(data.get("tool_call_id") or "")
                start = starts.get(tool_call_id, {})
                calls.append(
                    {
                        "name": data.get("tool_name") or start.get("tool_name") or "",
                        "arguments": start.get("arguments") or {},
                        "result": data.get("result"),
                        "status": "success" if data.get("status") == "success" else "error",
                    }
                )
        return calls

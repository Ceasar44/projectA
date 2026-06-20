from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING, Any

from app.domain.customer_support.memory import CrmMemoryIdentity
from app.domain.customer_support.prompt_builder import (
    CustomerSupportPromptContext,
    build_customer_support_prompt,
)
from app.infrastructure.db.models.conversations import Conversation
from app.infrastructure.db.models.knowledge import KnowledgeEntry
from app.infrastructure.db.models.operations import Settings
from app.infrastructure.integrations.ai import OpenAIProvider

if TYPE_CHECKING:
    from app.domain.customer_support.schemas import SupportAgentConfig
    from app.domain.customer_support.tools import SupportToolRegistry

from extern_agent.agent.protocol.models import LLMModel

CRM_EXTERN_AGENT_WORKSPACE = Path(__file__).resolve().parents[3] / ".runtime" / "crm_extern_agent"
CRM_EXTERN_AGENT_RUNTIME_CONFIG = {
    "agent_max_context_turns": 20,
    "agent_max_steps": 8,
    "agent_max_context_tokens": 50000,
    "conversation_persistence": False,
    "enable_thinking": False,
    "knowledge": False,
    "debug": False,
}
EXTERN_AGENT_WORKSPACE_TOOLS = {
    "read",
    "write",
    "edit",
    "bash",
    "grep",
    "find",
    "ls",
    "web_fetch",
    "send",
    "browser",
}


def _set_extern_agent_workspace(workspace_dir: Path) -> None:
    """Point extern_agent's global workspace config at the CRM workspace."""
    try:
        from extern_agent.config import conf

        runtime_config = conf()
        if isinstance(runtime_config, dict):
            for key, value in CRM_EXTERN_AGENT_RUNTIME_CONFIG.items():
                runtime_config.setdefault(key, value)
            runtime_config["agent_workspace"] = str(workspace_dir)
    except Exception:
        return None


class CrmExternAgentModel(LLMModel):
    """extern_agent LLMModel adapter backed by the backend OpenAI provider."""

    def __init__(self, settings: Settings) -> None:
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
        from extern_agent.agent.tools.base_tool import ToolStage

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
        from extern_agent.agent.tools.base_tool import ToolResult

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


@dataclass
class _CrmMemorySearchResult:
    path: str
    start_line: int
    end_line: int
    score: float
    snippet: str


class CrmTurnMemoryManager:
    """Per-turn memory manager that can read snapshots and collect drafts only."""

    def __init__(self, *, identity: CrmMemoryIdentity, snapshot: dict[str, Any]) -> None:
        self.identity = identity
        self.snapshot = snapshot
        self.drafts: list[dict[str, Any]] = []

    async def search(
        self,
        *,
        query: str,
        user_id: str | None = None,
        max_results: int = 10,
        min_score: float = 0.1,
        include_shared: bool = True,
    ) -> list[_CrmMemorySearchResult]:
        del user_id, include_shared
        query_terms = [term.casefold() for term in str(query or "").split() if term.strip()]
        matches: list[_CrmMemorySearchResult] = []
        for scope, items in self.snapshot.items():
            for index, item in enumerate(items or [], start=1):
                content = str((item or {}).get("content") or "")
                if not content:
                    continue
                text = " ".join(
                    [
                        str((item or {}).get("kind") or ""),
                        content,
                        str((item or {}).get("sourceCustomerMessage") or ""),
                    ]
                )
                score = self._score(text, query_terms)
                if score < min_score:
                    continue
                matches.append(
                    _CrmMemorySearchResult(
                        path=f"{scope}/memory#{index}",
                        start_line=1,
                        end_line=1,
                        score=score,
                        snippet=content[:500],
                    )
                )
        matches.sort(key=lambda result: result.score, reverse=True)
        return matches[:max_results]

    def get(self, path: str) -> str:
        try:
            scope, marker = path.split("/memory#", 1)
            index = int(marker) - 1
        except (ValueError, AttributeError):
            return ""
        items = self.snapshot.get(scope) or []
        if index < 0 or index >= len(items):
            return ""
        item = items[index] or {}
        return "\n".join(
            part
            for part in [
                f"Scope: {scope}",
                f"Kind: {item.get('kind') or 'note'}",
                f"Confidence: {item.get('confidence') or ''}",
                f"Content: {item.get('content') or ''}",
            ]
            if part.strip()
        )

    def remember(self, draft: dict[str, Any]) -> None:
        self.drafts.append(
            {
                "scope": draft.get("scope") or "conversation",
                "kind": draft.get("kind") or "note",
                "content": draft.get("content") or "",
                "confidence": draft.get("confidence") or 0.7,
            }
        )

    @staticmethod
    def _score(text: str, query_terms: list[str]) -> float:
        if not query_terms:
            return 0.3
        folded = text.casefold()
        hits = sum(1 for term in query_terms if term in folded)
        if hits == 0:
            return 0.0
        return min(1.0, 0.25 + hits / max(len(query_terms), 1))


class CrmMemorySearchTool:
    name = "memory_search"
    description = "Search this CRM customer's approved memory snapshot."
    params = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Natural language memory query."},
            "max_results": {"type": "integer", "default": 5},
            "min_score": {"type": "number", "default": 0.1},
        },
        "required": ["query"],
    }

    def __init__(self, memory_manager: CrmTurnMemoryManager, is_stale: Callable[[], bool]) -> None:
        from extern_agent.agent.tools.base_tool import ToolStage

        self.stage = ToolStage.PRE_PROCESS
        self.memory_manager = memory_manager
        self.is_stale = is_stale

    def get_json_schema(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "parameters": self.params}

    def execute_tool(self, params: dict[str, Any]):
        return self.execute(params)

    def execute(self, params: dict[str, Any]):
        from extern_agent.agent.tools.base_tool import ToolResult

        if self.is_stale():
            return ToolResult.fail({"success": False, "message": "This agent turn is stale."})
        results = asyncio.run(
            self.memory_manager.search(
                query=str(params.get("query") or ""),
                max_results=int(params.get("max_results") or 5),
                min_score=float(params.get("min_score") or 0.1),
            )
        )
        if not results:
            return ToolResult.success("No approved CRM memories matched.")
        lines = ["Found approved CRM memories:"]
        for index, result in enumerate(results, start=1):
            lines.append(f"{index}. {result.path} score={result.score:.2f}: {result.snippet}")
        return ToolResult.success("\n".join(lines))


class CrmMemoryGetTool:
    name = "memory_get"
    description = "Read an approved CRM memory item returned by memory_search."
    params = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path returned by memory_search."},
        },
        "required": ["path"],
    }

    def __init__(self, memory_manager: CrmTurnMemoryManager, is_stale: Callable[[], bool]) -> None:
        from extern_agent.agent.tools.base_tool import ToolStage

        self.stage = ToolStage.PRE_PROCESS
        self.memory_manager = memory_manager
        self.is_stale = is_stale

    def get_json_schema(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "parameters": self.params}

    def execute_tool(self, params: dict[str, Any]):
        return self.execute(params)

    def execute(self, params: dict[str, Any]):
        from extern_agent.agent.tools.base_tool import ToolResult

        if self.is_stale():
            return ToolResult.fail({"success": False, "message": "This agent turn is stale."})
        content = self.memory_manager.get(str(params.get("path") or ""))
        return ToolResult.success(content) if content else ToolResult.fail("Memory item not found.")


class CrmMemoryDraftTool:
    name = "memory_remember"
    description = (
        "Save a candidate CRM memory from this turn. This only creates a draft; "
        "the backend commits it if this is still the latest conversation turn."
    )
    params = {
        "type": "object",
        "properties": {
            "scope": {"type": "string", "enum": ["customer", "conversation"]},
            "kind": {"type": "string", "description": "preference, fact, decision, issue, or note."},
            "content": {"type": "string", "description": "Short durable memory content."},
            "confidence": {"type": "number", "default": 0.7},
        },
        "required": ["scope", "content"],
    }

    def __init__(self, memory_manager: CrmTurnMemoryManager, is_stale: Callable[[], bool]) -> None:
        from extern_agent.agent.tools.base_tool import ToolStage

        self.stage = ToolStage.PRE_PROCESS
        self.memory_manager = memory_manager
        self.is_stale = is_stale

    def get_json_schema(self) -> dict[str, Any]:
        return {"name": self.name, "description": self.description, "parameters": self.params}

    def execute_tool(self, params: dict[str, Any]):
        return self.execute(params)

    def execute(self, params: dict[str, Any]):
        from extern_agent.agent.tools.base_tool import ToolResult

        if self.is_stale():
            return ToolResult.fail({"success": False, "message": "This agent turn is stale."})
        self.memory_manager.remember(params)
        return ToolResult.success({"success": True, "message": "Memory draft captured."})


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
        memory_identity: CrmMemoryIdentity,
        memory_snapshot: dict[str, Any],
        is_stale: Callable[[], bool],
        cancel_event: Event | None,
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
            memory_identity,
            memory_snapshot,
            loop,
            is_stale,
            cancel_event,
        )

    def _reply_sync(
        self,
        settings: Settings,
        conversation: Conversation,
        customer_message: str,
        config: SupportAgentConfig,
        registry: SupportToolRegistry,
        knowledge_entries: list[KnowledgeEntry],
        memory_identity: CrmMemoryIdentity,
        memory_snapshot: dict[str, Any],
        loop: asyncio.AbstractEventLoop,
        is_stale: Callable[[], bool],
        cancel_event: Event | None,
    ) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
        from extern_agent.agent.protocol import Agent

        if is_stale():
            return "", {"provider": "extern_agent", "status": "superseded", "usage": {}}, []

        workspace_dir = self._prepare_workspace()
        memory_manager = CrmTurnMemoryManager(identity=memory_identity, snapshot=memory_snapshot)
        tools = [
            *self._build_tools(registry, config.allowed_tools, loop, is_stale),
            *self._build_memory_tools(memory_manager, is_stale),
        ]
        tools.extend(self._build_extern_agent_tools(workspace_dir, existing_tools=tools))
        system_prompt = self._build_system_prompt(
            settings,
            config,
            knowledge_entries,
            memory_manager,
            tools,
            conversation,
        )
        agent = Agent(
            system_prompt=system_prompt,
            description="CRM customer-support agent",
            model=CrmExternAgentModel(settings),
            tools=tools,
            output_mode="logger",
            max_steps=8,
            enable_skills=False,
            workspace_dir=str(workspace_dir),
            memory_manager=memory_manager,
        )
        agent.get_full_system_prompt = lambda skill_filter=None: system_prompt
        agent.messages = self._history_messages(conversation, customer_message)

        events: list[dict[str, Any]] = []

        def _on_event(event: dict[str, Any]) -> None:
            events.append(event)
            if is_stale() and cancel_event is not None:
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
                "memoryDrafts": memory_manager.drafts,
            },
            self._tool_calls_from_events(events),
        )

    @staticmethod
    def _prepare_workspace() -> Path:
        workspace_dir = CRM_EXTERN_AGENT_WORKSPACE
        workspace_dir.mkdir(parents=True, exist_ok=True)
        _set_extern_agent_workspace(workspace_dir)
        try:
            from extern_agent.agent.prompt import ensure_workspace

            ensure_workspace(str(workspace_dir), create_templates=True)
        except Exception:
            pass
        return workspace_dir

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
    def _build_memory_tools(
        memory_manager: CrmTurnMemoryManager,
        is_stale: Callable[[], bool],
    ) -> list[Any]:
        return [
            CrmMemorySearchTool(memory_manager, is_stale),
            CrmMemoryGetTool(memory_manager, is_stale),
            CrmMemoryDraftTool(memory_manager, is_stale),
        ]

    @staticmethod
    def _build_extern_agent_tools(workspace_dir: Path, existing_tools: list[Any]) -> list[Any]:
        _set_extern_agent_workspace(workspace_dir)
        existing_names = {
            str(getattr(tool, "name", "") or "")
            for tool in existing_tools
            if getattr(tool, "name", None)
        }
        loaded: list[Any] = []

        try:
            from extern_agent.agent.tools import ToolManager

            tool_manager = ToolManager()
            tool_manager.load_tools()
            tool_manager.refresh_mcp_if_changed()

            for tool_name in list(tool_manager.tool_classes.keys()):
                if tool_name in existing_names:
                    continue
                tool = tool_manager.create_tool(tool_name)
                if not tool:
                    continue
                CrmExternAgentAdapter._bind_workspace_to_tool(tool, workspace_dir)
                loaded.append(tool)
                existing_names.add(tool_name)

            for tool_name, mcp_tool in list(tool_manager._mcp_tool_instances.items()):
                if tool_name in existing_names:
                    continue
                loaded.append(mcp_tool)
                existing_names.add(tool_name)
        except Exception:
            return loaded

        return loaded

    @staticmethod
    def _bind_workspace_to_tool(tool: Any, workspace_dir: Path) -> None:
        if getattr(tool, "name", "") not in EXTERN_AGENT_WORKSPACE_TOOLS:
            return
        config = dict(getattr(tool, "config", None) or {})
        config["cwd"] = str(workspace_dir)
        tool.config = config
        if hasattr(tool, "cwd"):
            tool.cwd = str(workspace_dir)

    @staticmethod
    def _history_messages(conversation: Conversation, customer_message: str) -> list[dict[str, Any]]:
        rows = sorted(conversation.messages, key=CrmExternAgentAdapter._message_sort_key)
        if rows and rows[-1].role == "customer" and rows[-1].content == customer_message:
            rows = rows[:-1]
        history = []
        for item in rows[-12:]:
            role = "user" if item.role == "customer" else "assistant"
            history.append({"role": role, "content": [{"type": "text", "text": item.content}]})
        return history

    @staticmethod
    def _message_sort_key(item: Any) -> float:
        created_at = getattr(item, "created_at", None)
        return created_at.timestamp() if isinstance(created_at, datetime) else 0.0

    @staticmethod
    def _build_system_prompt(
        settings: Settings,
        config: SupportAgentConfig,
        knowledge_entries: list[KnowledgeEntry],
        memory_manager: CrmTurnMemoryManager,
        tools: list[Any] | None = None,
        conversation: Conversation | None = None,
    ) -> str:
        return build_customer_support_prompt(
            CustomerSupportPromptContext(
                settings=settings,
                config=config,
                knowledge_entries=knowledge_entries,
                memory_identity=memory_manager.identity,
                memory_snapshot=memory_manager.snapshot,
                tools=tools or [],
                runtime_info={
                    "model": settings.ai_model,
                    "channel": conversation.channel if conversation else None,
                    "conversation_id": (
                        conversation.id if conversation else memory_manager.identity.conversation_id
                    ),
                    "workspace": str(CRM_EXTERN_AGENT_WORKSPACE),
                },
            )
        )

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

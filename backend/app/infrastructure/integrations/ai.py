from typing import Protocol

import httpx


class AIProvider(Protocol):
    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict: ...


class OpenAIProvider:
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        base_url: str = "https://api.openai.com/v1",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.base_url = base_url.rstrip("/")

    async def chat(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        if not self.api_key:
            return {
                "provider": "openai",
                "status": "missing_api_key",
                "content": "AI is not configured yet. Please add an API key in Settings.",
            }

        payload: dict[str, object] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if tools:
            payload["tools"] = tools

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:500]
            return {
                "provider": "openai",
                "status": "http_error",
                "content": "The AI provider returned an error.",
                "error": detail,
            }
        except httpx.HTTPError as exc:
            return {
                "provider": "openai",
                "status": "network_error",
                "content": "The AI provider could not be reached.",
                "error": str(exc),
            }

        message = ((data.get("choices") or [{}])[0].get("message") or {})
        return {
            "provider": "openai",
            "status": "ok",
            "content": message.get("content") or "",
            "toolCalls": message.get("tool_calls") or [],
            "usage": data.get("usage") or {},
            "raw": data,
        }

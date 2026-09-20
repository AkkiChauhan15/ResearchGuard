"""Fixed-destination adapters for OpenAI-compatible chat APIs."""
from __future__ import annotations

import json
import os
from typing import Sequence

import httpx

from .base import ChatProviderError, ProviderMessage, ProviderReply


MAX_RESPONSE_BYTES = 64_000


class OpenAICompatibleProvider:
    def __init__(self, name: str, endpoint: str, key_env: str, *, headers: dict[str, str] | None = None):
        self.name = name
        self.endpoint = endpoint
        self.key_env = key_env
        self.extra_headers = headers or {}

    def complete(
        self,
        model: str,
        messages: Sequence[ProviderMessage],
        *,
        timeout_seconds: float,
        max_output_tokens: int,
    ) -> ProviderReply:
        key = os.environ.get(self.key_env, "").strip()
        if not key:
            raise ChatProviderError(f"{self.name} is not configured on the server.", "configuration")
        try:
            with httpx.Client(timeout=httpx.Timeout(timeout_seconds)) as client:
                with client.stream(
                    "POST",
                    self.endpoint,
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                        **self.extra_headers,
                    },
                    json={
                        "model": model,
                        "messages": [{"role": item.role, "content": item.content} for item in messages],
                        "max_tokens": max_output_tokens,
                        "temperature": 0.3,
                        "stream": False,
                    },
                ) as response:
                    self._raise_for_status(response.status_code)
                    raw = bytearray()
                    for chunk in response.iter_bytes():
                        raw.extend(chunk)
                        if len(raw) > MAX_RESPONSE_BYTES:
                            raise ChatProviderError(f"{self.name} returned an oversized response.", "malformed_response")
        except httpx.TimeoutException:
            raise ChatProviderError(f"{self.name} timed out. Retry later.", "timeout") from None
        except httpx.HTTPError:
            raise ChatProviderError(f"{self.name} is temporarily unreachable. Retry later.", "unavailable") from None
        try:
            payload = json.loads(raw)
            answer = payload["choices"][0]["message"]["content"]
            returned_model = payload.get("model") or model
            if not isinstance(answer, str) or not answer.strip():
                raise TypeError
            if not isinstance(returned_model, str) or not returned_model.strip():
                raise TypeError
            return ProviderReply(answer=answer.strip(), returned_model=returned_model.strip())
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError, IndexError, TypeError, AttributeError):
            raise ChatProviderError(f"{self.name} returned a malformed response.", "malformed_response") from None

    def _raise_for_status(self, status_code: int) -> None:
        if status_code in {401, 403}:
            raise ChatProviderError(f"{self.name} rejected its server API key or account access.", "configuration")
        if status_code == 404:
            raise ChatProviderError(f"The selected {self.name} model is unavailable.", "model_unavailable")
        if status_code == 429:
            raise ChatProviderError(f"{self.name} free quota or rate limit is exhausted. Retry later.", "rate_limited")
        if status_code in {408, 504}:
            raise ChatProviderError(f"{self.name} timed out. Retry later.", "timeout")
        if status_code >= 500:
            raise ChatProviderError(f"{self.name} is temporarily unavailable. Retry later.", "unavailable")
        if status_code >= 400:
            raise ChatProviderError(f"{self.name} rejected the chat request.", "request_rejected")


def groq_provider() -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        "Groq",
        "https://api.groq.com/openai/v1/chat/completions",
        "GROQ_API_KEY",
    )


def openrouter_provider() -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        "OpenRouter",
        "https://openrouter.ai/api/v1/chat/completions",
        "OPENROUTER_API_KEY",
        headers={"X-Title": "Research Guard AI"},
    )


def nvidia_provider() -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        "NVIDIA NIM",
        "https://integrate.api.nvidia.com/v1/chat/completions",
        "NVIDIA_NIM_API_KEY",
    )

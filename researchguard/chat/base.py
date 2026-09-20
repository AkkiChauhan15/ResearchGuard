"""Shared types and errors for the optional general chat providers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class ProviderMessage:
    role: str
    content: str


@dataclass(frozen=True)
class ProviderReply:
    answer: str
    returned_model: str


class ChatProviderError(RuntimeError):
    """A safe provider failure that may be considered for explicit fallback."""

    def __init__(self, detail: str, category: str):
        super().__init__(detail)
        self.detail = detail
        self.category = category

    @property
    def fallback_eligible(self) -> bool:
        return self.category in {"rate_limited", "timeout", "unavailable", "model_unavailable"}


class ChatProvider(Protocol):
    name: str

    def complete(
        self,
        model: str,
        messages: Sequence[ProviderMessage],
        *,
        timeout_seconds: float,
        max_output_tokens: int,
    ) -> ProviderReply: ...

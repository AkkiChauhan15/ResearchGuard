"""Runtime structured model-provider selection with no silent fallback."""
from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel

from .base import ModelProvider, ProviderStatus
from .openai_compatible import SPECS, compatible_provider


def _gemini_provider():
    """Import the legacy-compatible provider only when it is explicitly selected."""
    from .gemini import GeminiProvider

    return GeminiProvider


def provider_status() -> ProviderStatus:
    provider = os.environ.get("LLM_PROVIDER", "groq").strip().lower()
    if provider in {"openai", "legacy_openai"}:
        return ProviderStatus(
            provider="legacy_openai",
            state="unavailable_provider_disabled",
            detail="The legacy OpenAI adapter is disabled and is not an authorized fallback.",
        )
    if provider == "gemini":
        return _gemini_provider().status()
    if provider in SPECS:
        return compatible_provider(provider).status()
    if provider not in {"gemini", *SPECS}:
        return ProviderStatus(
            provider=provider or "unset",
            state="unavailable_invalid_configuration",
            detail="LLM_PROVIDER must be groq, openrouter, nvidia, or gemini. No provider was selected automatically.",
        )
    raise AssertionError("Unreachable provider selection.")


def configured() -> bool:
    return provider_status().available


def selected_provider() -> ModelProvider:
    status = provider_status()
    if not status.available:
        raise ValueError(status.detail)
    if status.provider == "gemini":
        return _gemini_provider()()
    return compatible_provider(status.provider)


def generate_structured(
    output_type: type[BaseModel],
    task: str,
    payload: Any,
    *,
    system_instruction: str,
    task_instruction: str,
):
    return selected_provider().generate(
        output_type,
        task,
        payload,
        system_instruction=system_instruction,
        task_instruction=task_instruction,
    )


__all__ = [
    "configured",
    "generate_structured",
    "provider_status",
    "selected_provider",
]

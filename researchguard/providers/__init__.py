"""Runtime model-provider selection.

Only Gemini Free Tier is authorized for the current local build. The legacy
OpenAI implementation is retained in ``openai_legacy.py`` for provenance, but
is deliberately not selectable here.
"""
from __future__ import annotations

import os
from typing import Any

from pydantic import BaseModel

from .base import ModelProvider, ProviderStatus
from .gemini import GeminiProvider


def provider_status() -> ProviderStatus:
    provider = os.environ.get("LLM_PROVIDER", "gemini").strip().lower()
    if provider in {"openai", "legacy_openai"}:
        return ProviderStatus(
            provider="legacy_openai",
            state="unavailable_provider_disabled",
            detail="The legacy OpenAI adapter is disabled and is not an authorized fallback.",
        )
    if provider != "gemini":
        return ProviderStatus(
            provider=provider or "unset",
            state="unavailable_invalid_configuration",
            detail="LLM_PROVIDER must be gemini for the approved local configuration.",
        )
    return GeminiProvider.status()


def configured() -> bool:
    return provider_status().available


def selected_provider() -> ModelProvider:
    status = provider_status()
    if not status.available:
        raise ValueError(status.detail)
    return GeminiProvider()


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

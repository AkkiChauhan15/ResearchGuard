"""Versioned provider/model allowlist and server-only availability checks."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path


CONFIG_PATH = Path(__file__).with_name("models.json")
KEY_ENV = {
    "groq": "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "nvidia": "NVIDIA_NIM_API_KEY",
}
FREE_CONFIRMATION_ENV = {
    "groq": "GROQ_FREE_TIER_CONFIRMED",
    "gemini": "GEMINI_FREE_TIER_CONFIRMED",
    "nvidia": "NVIDIA_NIM_FREE_TIER_CONFIRMED",
}


def _true(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class ChatModel:
    id: str
    label: str


@dataclass(frozen=True)
class ChatProviderConfig:
    id: str
    display_name: str
    models: tuple[ChatModel, ...]

    @property
    def configured(self) -> bool:
        if not os.environ.get(KEY_ENV[self.id], "").strip():
            return False
        confirmation = FREE_CONFIRMATION_ENV.get(self.id)
        return confirmation is None or _true(confirmation)

    @property
    def state(self) -> str:
        if not os.environ.get(KEY_ENV[self.id], "").strip():
            return "missing_api_key"
        confirmation = FREE_CONFIRMATION_ENV.get(self.id)
        if confirmation and not _true(confirmation):
            return "free_tier_unconfirmed"
        return "configured"


def load_chat_config() -> tuple[str, dict[str, ChatProviderConfig]]:
    raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    providers: dict[str, ChatProviderConfig] = {}
    for provider_id, item in raw["providers"].items():
        models = tuple(ChatModel(id=model["id"], label=model["label"]) for model in item["models"])
        if not models or len({model.id for model in models}) != len(models):
            raise RuntimeError(f"Invalid chat model configuration for {provider_id}.")
        providers[provider_id] = ChatProviderConfig(
            id=provider_id,
            display_name=item["display_name"],
            models=models,
        )
    if set(providers) != set(KEY_ENV):
        raise RuntimeError("Chat provider configuration does not match the implemented adapters.")
    return raw["version"], providers

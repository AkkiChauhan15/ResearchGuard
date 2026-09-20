"""One bounded public/synthetic live check for a configured chat provider."""
from __future__ import annotations

import argparse

from researchguard.chat import ChatProviderError, ChatService, ProviderMessage
from researchguard.local_env import load_local_env
from researchguard.settings import Settings


def main() -> None:
    load_local_env()
    parser = argparse.ArgumentParser(description="Verify one configured Research Guard chat provider")
    parser.add_argument("--provider", choices=("groq", "openrouter", "gemini", "nvidia"), default="gemini")
    args = parser.parse_args()
    settings = Settings.from_env()
    service = ChatService(
        fallback_enabled=False,
        provider_timeout_seconds=settings.chat_provider_timeout_seconds,
        max_output_tokens=min(settings.chat_max_output_tokens, 256),
    )
    provider = service.providers[args.provider]
    if not provider.configured:
        raise SystemExit(f"BLOCKED: {service._unavailable_detail(provider)}")
    try:
        result = service.complete(
            args.provider,
            provider.models[0].id,
            (ProviderMessage("user", "In two sentences, explain why a model answer is not scientific evidence."),),
            allow_fallback=False,
            total_timeout_seconds=settings.chat_timeout_seconds,
        )
    except ChatProviderError as exc:
        raise SystemExit(f"BLOCKED: {exc.detail}") from None
    print("PASS: bounded live chat response received")
    print(f"provider={result.provider}")
    print(f"requested_model={result.requested_model}")
    print(f"returned_model={result.model}")
    print(f"answer_characters={len(result.answer)}")
    print("fallback_used=false")
    print("Scientific correctness was not established by this connectivity check.")


if __name__ == "__main__":
    main()

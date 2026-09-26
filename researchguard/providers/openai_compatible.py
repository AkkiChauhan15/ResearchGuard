"""Bounded structured-output adapters for approved OpenAI-compatible free APIs."""
from __future__ import annotations

from dataclasses import dataclass
import json
import os
import threading
import time
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from ..schemas import ModelRun
from .base import ProviderStatus


PROMPT_VERSION = "researchguard-2026-09-26-compatible-v3"
MAX_INPUT_BYTES = 20_000
MAX_OUTPUT_BYTES = 64_000
MAX_OUTPUT_TOKENS = {"extraction": 2_048, "assessment": 2_048}
REQUEST_TIMEOUT_SECONDS = 60.0
CONCURRENCY_WAIT_SECONDS = 5
_CONCURRENCY = threading.BoundedSemaphore(2)
_UNSUPPORTED_SCHEMA_HINTS = frozenset({
    "default",
    "examples",
    "maxItems",
    "maxLength",
    "minItems",
    "minLength",
    "title",
})


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    display_name: str
    endpoint: str
    key_env: str
    confirmation_env: str | None
    extraction_model_env: str
    assessment_model_env: str
    default_model: str
    allowed_models: frozenset[str]
    schema_mode: str
    extra_headers: dict[str, str] | None = None


SPECS = {
    "groq": ProviderSpec(
        id="groq",
        display_name="Groq",
        endpoint="https://api.groq.com/openai/v1/chat/completions",
        key_env="GROQ_API_KEY",
        confirmation_env="GROQ_FREE_TIER_CONFIRMED",
        extraction_model_env="GROQ_EXTRACTION_MODEL",
        assessment_model_env="GROQ_ASSESSMENT_MODEL",
        default_model="openai/gpt-oss-20b",
        allowed_models=frozenset({"openai/gpt-oss-20b"}),
        schema_mode="response_format",
    ),
    "openrouter": ProviderSpec(
        id="openrouter",
        display_name="OpenRouter",
        endpoint="https://openrouter.ai/api/v1/chat/completions",
        key_env="OPENROUTER_API_KEY",
        confirmation_env=None,
        extraction_model_env="OPENROUTER_EXTRACTION_MODEL",
        assessment_model_env="OPENROUTER_ASSESSMENT_MODEL",
        default_model="openrouter/free",
        allowed_models=frozenset({"openrouter/free"}),
        schema_mode="response_format",
        extra_headers={"X-Title": "Research Guard AI"},
    ),
    "nvidia": ProviderSpec(
        id="nvidia",
        display_name="NVIDIA NIM",
        endpoint="https://integrate.api.nvidia.com/v1/chat/completions",
        key_env="NVIDIA_NIM_API_KEY",
        confirmation_env="NVIDIA_NIM_FREE_TIER_CONFIRMED",
        extraction_model_env="NVIDIA_NIM_EXTRACTION_MODEL",
        assessment_model_env="NVIDIA_NIM_ASSESSMENT_MODEL",
        default_model="meta/llama-3.3-70b-instruct",
        allowed_models=frozenset({
            "meta/llama-3.1-8b-instruct",
            "meta/llama-3.3-70b-instruct",
        }),
        schema_mode="guided_json",
    ),
}


def _true(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes"}


def _portable_schema(value: Any) -> Any:
    """Keep the constrained shape while leaving field bounds to Pydantic.

    The providers implement different JSON Schema subsets. Required fields, closed
    objects, enums, arrays and references are retained for constrained decoding;
    application validation remains authoritative for string/array length limits.
    """
    if isinstance(value, dict):
        return {
            key: _portable_schema(item)
            for key, item in value.items()
            if key not in _UNSUPPORTED_SCHEMA_HINTS
        }
    if isinstance(value, list):
        return [_portable_schema(item) for item in value]
    return value


class CompatibleStructuredProvider:
    def __init__(self, provider_id: str):
        self.spec = SPECS[provider_id]

    def _models(self) -> tuple[str, str]:
        return (
            os.environ.get(self.spec.extraction_model_env, self.spec.default_model).strip(),
            os.environ.get(self.spec.assessment_model_env, self.spec.default_model).strip(),
        )

    def status(self) -> ProviderStatus:
        extraction_model, assessment_model = self._models()
        if not os.environ.get(self.spec.key_env, "").strip():
            return ProviderStatus(
                self.spec.id,
                "unavailable_missing_credentials",
                f"Live AI unavailable: configure {self.spec.key_env} on the server. No demonstration result was substituted.",
                extraction_model,
                assessment_model,
            )
        if self.spec.confirmation_env and not _true(self.spec.confirmation_env):
            return ProviderStatus(
                self.spec.id,
                "unavailable_free_tier_unconfirmed",
                f"Live AI unavailable: confirm this {self.spec.display_name} account uses free access with no billing, then set {self.spec.confirmation_env}=true.",
                extraction_model,
                assessment_model,
            )
        unsupported = sorted({extraction_model, assessment_model} - self.spec.allowed_models)
        if unsupported:
            return ProviderStatus(
                self.spec.id,
                "unavailable_model_not_free_tier",
                f"Configured {self.spec.display_name} model is not on Research Guard's structured free-provider allowlist: "
                + ", ".join(unsupported)
                + ". No paid model or fallback was used.",
                extraction_model,
                assessment_model,
            )
        return ProviderStatus(
            self.spec.id,
            "configured",
            f"{self.spec.display_name} free-access configuration is present; API access is checked when a model request is made.",
            extraction_model,
            assessment_model,
        )

    def generate(
        self,
        output_type: type[BaseModel],
        task: str,
        payload: Any,
        *,
        system_instruction: str,
        task_instruction: str,
    ) -> tuple[BaseModel, ModelRun]:
        status = self.status()
        if not status.available:
            raise ValueError(status.detail)
        if task not in MAX_OUTPUT_TOKENS:
            raise ValueError("Unsupported model task.")
        model = status.extraction_model if task == "extraction" else status.assessment_model
        assert model is not None
        encoded_input = json.dumps(
            {"task": task, "data": payload},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        if len(encoded_input) > MAX_INPUT_BYTES:
            raise ValueError(
                f"Model input exceeds the {MAX_INPUT_BYTES}-byte limit. Reduce the input or retrieved passages; no request was sent."
            )
        if not _CONCURRENCY.acquire(timeout=CONCURRENCY_WAIT_SECONDS):
            raise ValueError(
                f"{self.spec.display_name} request capacity is busy. Retry after the current local requests finish."
            )

        schema = _portable_schema(output_type.model_json_schema())
        request_payload: dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_instruction + "\n" + task_instruction},
                {"role": "user", "content": encoded_input.decode("utf-8")},
            ],
            "temperature": 0,
            "stream": False,
        }
        if self.spec.id == "groq":
            # Groq documents max_completion_tokens as the current field. Low reasoning
            # leaves more of the free-plan token budget for the structured answer.
            request_payload["max_completion_tokens"] = MAX_OUTPUT_TOKENS[task]
            request_payload["reasoning_effort"] = "low"
            request_payload["reasoning_format"] = "hidden"
        else:
            request_payload["max_tokens"] = MAX_OUTPUT_TOKENS[task]
        if self.spec.schema_mode == "guided_json":
            request_payload["guided_json"] = schema
        else:
            request_payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": f"researchguard_{task}",
                    "strict": True,
                    "schema": schema,
                },
            }
        if self.spec.id == "openrouter":
            request_payload["provider"] = {"require_parameters": True}

        try:
            response_payload = self._request(request_payload)
            choice = response_payload["choices"][0]
            if choice.get("finish_reason") not in {None, "stop"}:
                raise ValueError(f"{self.spec.display_name} returned an incomplete response; no result was produced.")
            message = choice["message"]
            if message.get("refusal"):
                raise ValueError(f"{self.spec.display_name} refused the structured request; no result was produced.")
            raw = message["content"]
            returned_model = response_payload.get("model")
            if not isinstance(raw, str) or not raw.strip():
                raise TypeError
            if len(raw.encode("utf-8")) > MAX_OUTPUT_BYTES:
                raise ValueError(f"{self.spec.display_name} output exceeded the local response limit and was rejected.")
            if not isinstance(returned_model, str) or not returned_model.strip():
                raise TypeError
            parsed = output_type.model_validate_json(raw)
            return parsed, ModelRun(
                provider=self.spec.id,
                task=task,
                requested_model=model,
                returned_model=returned_model.strip(),
                prompt_version=PROMPT_VERSION,
                validation=[
                    f"{self.spec.display_name} structured output passed application Pydantic validation.",
                    "No provider tools, web search, or paid fallback were configured.",
                ],
            )
        except (ValidationError, json.JSONDecodeError, KeyError, IndexError, TypeError, AttributeError):
            raise ValueError(f"Malformed {self.spec.display_name} output rejected; no result was produced.") from None
        finally:
            _CONCURRENCY.release()

    def _request(self, request_payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {os.environ[self.spec.key_env]}",
            "Content-Type": "application/json",
            **(self.spec.extra_headers or {}),
        }
        for attempt in range(2):
            try:
                with httpx.Client(timeout=httpx.Timeout(REQUEST_TIMEOUT_SECONDS)) as client:
                    with client.stream(
                        "POST",
                        self.spec.endpoint,
                        headers=headers,
                        json=request_payload,
                    ) as response:
                        if response.status_code >= 400:
                            if response.status_code in {500, 502, 503, 504} and attempt == 0:
                                time.sleep(0.25)
                                continue
                            raise ValueError(self._api_error(response.status_code))
                        raw = bytearray()
                        for chunk in response.iter_bytes():
                            raw.extend(chunk)
                            if len(raw) > MAX_OUTPUT_BYTES:
                                raise ValueError(f"{self.spec.display_name} response exceeded the local response limit and was rejected.")
                parsed = json.loads(raw)
                if not isinstance(parsed, dict):
                    raise TypeError
                return parsed
            except httpx.TransportError:
                if attempt == 0:
                    time.sleep(0.25)
                    continue
                raise ValueError(f"{self.spec.display_name} timed out or is unreachable after a bounded retry. Retry later; no fallback was used.") from None
        raise ValueError(f"{self.spec.display_name} request failed without producing a result.")

    def _api_error(self, code: int) -> str:
        if code == 400:
            return f"{self.spec.display_name} rejected the structured-output request. Check the configured model and schema support; no fallback was used."
        if code in {401, 403}:
            return f"{self.spec.display_name} authentication or account access failed. Check the server API key and free-access configuration; no fallback was used."
        if code == 404:
            return f"The configured {self.spec.display_name} model is unavailable; no fallback was used."
        if code == 413:
            return f"{self.spec.display_name} rejected the bounded request as too large. Narrow the retrieved evidence and retry; no fallback was used."
        if code == 422:
            return f"{self.spec.display_name} could not complete the structured request for this evidence. Retry once or narrow the retrieved evidence; no fallback was used."
        if code == 424:
            return f"{self.spec.display_name} reported a failed dependency. Retry later; no fallback was used."
        if code == 429:
            return f"{self.spec.display_name} free quota or rate limit is exhausted. Wait for quota reset; no paid fallback was used."
        if code in {408, 504}:
            return f"{self.spec.display_name} timed out. Retry later; no fallback was used."
        if code == 498:
            return f"{self.spec.display_name} free-tier capacity is temporarily unavailable. Retry later; no paid fallback was used."
        if code == 499:
            return f"{self.spec.display_name} cancelled the request before completion. Retry later; no fallback was used."
        if code >= 500:
            return f"{self.spec.display_name} is temporarily unavailable after a bounded retry. Retry later; no fallback was used."
        return f"{self.spec.display_name} rejected the model request; no result or fallback was used."


def compatible_provider(provider_id: str) -> CompatibleStructuredProvider:
    return CompatibleStructuredProvider(provider_id)

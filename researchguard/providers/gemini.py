"""Bounded Gemini Developer API structured-output adapter."""
from __future__ import annotations

import json
import os
import threading
from typing import Any

from google import genai
from google.genai import errors, types
import httpx
from pydantic import BaseModel, ValidationError

from ..schemas import ModelRun
from .base import ProviderStatus


PROVIDER_NAME = "gemini"
PROMPT_VERSION = "researchguard-2026-09-26-gemini-v3"
DEFAULT_MODEL = "gemini-3.8-flash"
# Verified against the official pricing table on 2026-09-18. Keep this narrow
# and recheck current pricing before adding a model identifier.
FREE_TIER_MODELS = frozenset({"gemini-3.8-flash"})
MAX_INPUT_BYTES = 20_000
MAX_OUTPUT_BYTES = 64_000
MAX_OUTPUT_TOKENS = {"extraction": 2_048, "assessment": 2_048}
REQUEST_TIMEOUT_MS = 60_000
CONCURRENCY_WAIT_SECONDS = 5
_CONCURRENCY = threading.BoundedSemaphore(2)


def _models() -> tuple[str, str]:
    return (
        os.environ.get("GEMINI_EXTRACTION_MODEL", DEFAULT_MODEL).strip(),
        os.environ.get("GEMINI_ASSESSMENT_MODEL", DEFAULT_MODEL).strip(),
    )


def _confirmed_free_tier() -> bool:
    return os.environ.get("GEMINI_FREE_TIER_CONFIRMED", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }


class GeminiProvider:
    @staticmethod
    def status() -> ProviderStatus:
        extraction_model, assessment_model = _models()
        if not os.environ.get("GEMINI_API_KEY", "").strip():
            return ProviderStatus(
                PROVIDER_NAME,
                "unavailable_missing_credentials",
                "Live AI unavailable: configure GEMINI_API_KEY on the server. No demonstration result was substituted.",
                extraction_model,
                assessment_model,
            )
        if not _confirmed_free_tier():
            return ProviderStatus(
                PROVIDER_NAME,
                "unavailable_free_tier_unconfirmed",
                "Live AI unavailable: confirm in Google AI Studio that the project is on Free Tier with no billing, then set GEMINI_FREE_TIER_CONFIRMED=true.",
                extraction_model,
                assessment_model,
            )
        unsupported = sorted(
            {extraction_model, assessment_model} - FREE_TIER_MODELS
        )
        if unsupported:
            return ProviderStatus(
                PROVIDER_NAME,
                "unavailable_model_not_free_tier",
                "Configured Gemini model is not on Research Guard's verified Free Tier allowlist: "
                + ", ".join(unsupported)
                + ". No paid model or fallback was used.",
                extraction_model,
                assessment_model,
            )
        return ProviderStatus(
            PROVIDER_NAME,
            "configured",
            "Gemini Free Tier configuration is present; API access is checked when a model request is made.",
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
            raise ValueError("Gemini request capacity is busy. Retry after the current local requests finish.")

        client = None
        try:
            client = genai.Client(
                api_key=os.environ["GEMINI_API_KEY"],
                http_options=types.HttpOptions(
                    timeout=REQUEST_TIMEOUT_MS,
                    retry_options=types.HttpRetryOptions(
                        attempts=2,
                        initial_delay=0.25,
                        max_delay=0.5,
                        exp_base=2.0,
                        jitter=0.1,
                        # A 429 may be daily Free Tier exhaustion. Do not hide it
                        # behind retries or a paid fallback.
                        http_status_codes=[500, 502, 503, 504],
                    ),
                ),
            )
            response = client.models.generate_content(
                model=model,
                contents=encoded_input.decode("utf-8"),
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction + "\n" + task_instruction,
                    temperature=0,
                    candidate_count=1,
                    max_output_tokens=MAX_OUTPUT_TOKENS[task],
                    response_mime_type="application/json",
                    # The API's JSON Schema path supports Pydantic's strict
                    # additionalProperties fields. The older response_schema/OpenAPI
                    # conversion rejects them for Gemini 3.8 Flash.
                    response_json_schema=output_type.model_json_schema(),
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(
                        disable=True
                    ),
                ),
            )
            if not response.candidates or response.candidates[0].finish_reason != types.FinishReason.STOP:
                raise ValueError("The Gemini response was incomplete or blocked; no result was produced.")
            raw = response.text
            if not isinstance(raw, str) or not raw.strip():
                raise ValueError("Malformed Gemini output rejected; no result was produced.")
            if len(raw.encode("utf-8")) > MAX_OUTPUT_BYTES:
                raise ValueError("Gemini output exceeded the local response limit and was rejected.")
            parsed = output_type.model_validate_json(raw)
            returned_model = response.model_version
            if not isinstance(returned_model, str) or not returned_model.strip():
                raise ValueError("The Gemini response did not identify the model version used.")
            return parsed, ModelRun(
                provider=PROVIDER_NAME,
                task=task,
                requested_model=model,
                returned_model=returned_model,
                prompt_version=PROMPT_VERSION,
                validation=[
                    "Gemini structured-output schema passed application validation.",
                    "No provider tools, search grounding, or cached content were configured.",
                ],
            )
        except errors.APIError as exc:
            raise ValueError(_api_error_message(exc.code)) from None
        except httpx.TransportError:
            raise ValueError(
                "Gemini timed out or is unreachable after bounded retries. Retry later; no fallback was used."
            ) from None
        except (ValidationError, json.JSONDecodeError, KeyError, TypeError, AttributeError):
            raise ValueError("Malformed Gemini output rejected; no result was produced.") from None
        finally:
            if client is not None:
                client.close()
            _CONCURRENCY.release()


def _api_error_message(code: int) -> str:
    if code == 400:
        return "Gemini rejected the request configuration or structured-output schema. Check the server adapter; no fallback was used."
    if code in {401, 403}:
        return "Gemini authentication or request access failed. Check the server API key and Free Tier project permissions; no fallback was used."
    if code == 404:
        return "The configured Gemini model is unavailable in this project. Check Free Tier model access; no paid model or fallback was used."
    if code == 429:
        return "Gemini Free Tier rate limit or quota is exhausted. Wait for quota reset; no paid fallback or demonstration result was used."
    if code in {500, 502, 503, 504}:
        return "Gemini is temporarily unavailable or experiencing high demand after bounded retries. Retry later; no fallback result was used."
    return "Gemini request failed without producing a result. Check the local server configuration; no fallback was used."

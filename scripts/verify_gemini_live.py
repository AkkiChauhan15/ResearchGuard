"""Run one minimal Gemini extraction and assessment after Free Tier confirmation.

This script never enables billing or selects another provider/model. It prints
provenance and validation metadata, not the API key or source passage body.
"""
from __future__ import annotations

import hashlib
import json

from researchguard.assessment import Extraction, call_model, validate_assessment
from researchguard.providers import provider_status
from researchguard.schemas import Assessment, Passage, Source


def main() -> int:
    status = provider_status()
    if not status.available:
        print(json.dumps({
            "status": "blocked",
            "provider": status.provider,
            "state": status.state,
            "detail": status.detail,
            "live_calls_attempted": 0,
        }, indent=2))
        return 2

    claim_text = "The synthetic sample showed more fluorescent spots."
    source_text = (
        "The synthetic sample showed more fluorescent spots under the measured "
        "condition. This observation alone does not establish a biological mechanism."
    )
    source = Source(
        source_id="source_synthetic_live_check",
        retrieval_run_id="retrieval_synthetic_live_check",
        url="urn:researchguard:synthetic-live-check",
        category="synthetic",
        title="Synthetic public-safe Gemini verification passage",
        access_level="full text",
        content_sha256=hashlib.sha256(source_text.encode()).hexdigest(),
        passages=[Passage(text=source_text, location="Synthetic passage 1")],
        limitations=["Synthetic verification text; not scientific evidence."],
    )

    extraction, extraction_run = call_model(
        Extraction,
        "extraction",
        {
            "text": claim_text,
            "intended_use": "topic understanding",
            "context": {},
            "source_urls": [],
        },
    )
    if any(item.original_span not in claim_text for item in extraction.claims):
        raise ValueError("Live extraction failed original-span validation.")

    assessment, assessment_run = call_model(
        Assessment,
        "assessment",
        {
            "claim": claim_text,
            "intended_use": "topic understanding",
            "user_reported_context": {},
            "sources": [source.model_dump()],
        },
    )
    deterministic_checks = validate_assessment(assessment, [source])
    assessment_run.source_ids = [source.source_id]
    assessment_run.validation.extend(deterministic_checks)

    print(json.dumps({
        "status": "passed",
        "provider": status.provider,
        "free_tier_confirmation": "operator attested with GEMINI_FREE_TIER_CONFIRMED=true",
        "requested_models": {
            "extraction": extraction_run.requested_model,
            "assessment": assessment_run.requested_model,
        },
        "returned_models": {
            "extraction": extraction_run.returned_model,
            "assessment": assessment_run.returned_model,
        },
        "prompt_versions": {
            "extraction": extraction_run.prompt_version,
            "assessment": assessment_run.prompt_version,
        },
        "sources": [{
            "source_id": source.source_id,
            "access_level": source.access_level,
            "content_sha256": source.content_sha256,
        }],
        "validation": {
            "extraction": extraction_run.validation + ["Original spans matched synthetic input."],
            "assessment": assessment_run.validation,
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

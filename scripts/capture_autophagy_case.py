"""Capture a bounded, public-only Phase H autophagy source snapshot.

The browser export remains a curated demonstration. This companion artifact records
fresh adapter results separately and leaves model output null when the selected evidence
provider is unavailable.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from uuid import uuid4

from researchguard.providers import provider_status
from researchguard.retrieval import MANUAL, PRODUCT, retrieve_url


OUTPUT = Path("artifacts/competition-demo/autophagy-case-record.json")
DEMO_EXPORT = Path("artifacts/competition-demo/autophagy-demo-export.json")


def select_passages(source, needles: tuple[str, ...]) -> list[dict[str, str]]:
    selected = []
    for needle in needles:
        passage = next(
            (
                item for item in source.passages
                if needle.lower() in " ".join(item.text.split()).lower()
            ),
            None,
        )
        if passage is None:
            raise RuntimeError(f"Expected public passage was not found for {source.url}.")
        selected.append(passage.model_dump())
    return selected


def source_record(source, needles: tuple[str, ...]) -> dict:
    return {
        "source_id": source.source_id,
        "retrieval_run_id": source.retrieval_run_id,
        "url": source.url,
        "category": source.category,
        "title": source.title,
        "authors": source.authors,
        "date": source.date,
        "doi": source.doi,
        "pmid": source.pmid,
        "pmcid": source.pmcid,
        "access_level": source.access_level,
        "retrieved_at": source.retrieved_at,
        "document_version": source.document_version,
        "content_sha256": source.content_sha256,
        "passage_count": len(source.passages),
        "evidence_passages": select_passages(source, needles),
        "limitations": source.limitations,
    }


def main() -> None:
    if not DEMO_EXPORT.is_file():
        raise RuntimeError("Run scripts/browser_react_smoke.cjs with SCREENSHOT_DIR first.")
    demo = json.loads(DEMO_EXPORT.read_text())
    run = f"phase_h_autophagy_{uuid4().hex}"
    pubmed = retrieve_url("https://pubmed.ncbi.nlm.nih.gov/25484088/", run)[0]
    pmc = retrieve_url("https://pmc.ncbi.nlm.nih.gov/articles/PMC4502790/", run)[0]
    product = retrieve_url(PRODUCT, run)[0]
    manual = retrieve_url(MANUAL, run)[0]
    model = provider_status()

    record = {
        "artifact_generated_at": datetime.now(timezone.utc).isoformat(),
        "case": "When more fluorescent spots do not mean more cellular activity",
        "input_origin": "reconstructed synthetic competition input; not a historical transcript",
        "input": demo["original_input"],
        "browser_demo_review_id": demo["review_id"],
        "browser_demo_created_at": demo["created_at"],
        "researcher_decision": demo["claims"][0]["decision"],
        "curated_suggested_wording": demo["claims"][0]["assessment"]["suggested_wording"],
        "fresh_retrieval_scope": (
            "Read-only adapter verification performed after the browser demo. These fresh records "
            "are not represented as the curated demo's runtime retrieval."
        ),
        "sources": [
            source_record(pubmed, ("flow of material",)),
            source_record(pmc, ("flow of material",)),
            source_record(product, ("lysosomal function is inhibited",)),
            source_record(manual, ("accumulation of autophagosomes can represent either",)),
        ],
        "model": {
            "output": None,
            "provider": model.provider,
            "state": model.state,
            "detail": model.detail,
            "extraction_model_requested": model.extraction_model,
            "assessment_model_requested": model.assessment_model,
            "live_calls_attempted": 0,
        },
        "scientific_review_status": (
            "No knowledgeable human scientific review was performed in Phase H. "
            "The researcher wording above is a competition-demo edit."
        ),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "status": "captured",
        "output": str(OUTPUT),
        "source_count": len(record["sources"]),
        "access_levels": [source["access_level"] for source in record["sources"]],
        "model_state": record["model"]["state"],
        "model_calls_attempted": 0,
    }, indent=2))


if __name__ == "__main__":
    main()

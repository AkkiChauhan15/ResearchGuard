"""Read-only Phase D verification against exact supported public sources.

This script prints metadata and hashes, not retrieved passages. It performs no model
call and does not write source responses to the repository.
"""
from __future__ import annotations

from datetime import datetime
import json
import re
import xml.etree.ElementTree as ET

import researchguard.retrieval as retrieval
from researchguard.retrieval import MANUAL, PRODUCT, manual_record, pmc_record, product_record
from researchguard.transport import FetchError, fetch


DEMO_PMCID = "PMC4502790"
OPEN_FULL_TEXT_PMCID = "PMC8270360"  # Current official PMC EFetch example article.


def check_source(source, run: str) -> None:
    assert source.source_id.startswith("src_")
    assert source.retrieval_run_id == run
    datetime.fromisoformat(source.retrieved_at)
    assert re.fullmatch(r"[0-9a-f]{64}", source.content_sha256)
    assert source.integrity is not None
    for passage in source.passages:
        # PDF page extracts intentionally preserve layout whitespace.
        assert passage.text.strip()
        assert passage.location


def main() -> None:
    run = "retrieval_phase_d_live"
    calls: list[tuple[str, dict[str, str | int]]] = []
    original_ncbi = retrieval.ncbi

    def recording_ncbi(endpoint, params):
        calls.append((endpoint, dict(params)))
        return original_ncbi(endpoint, params)

    retrieval.ncbi = recording_ncbi
    try:
        pubmed = retrieval.search_pubmed("autophagosome flux measurement", run)
    finally:
        retrieval.ncbi = original_ncbi
    assert pubmed
    fetch_ids = [str(params["id"]) for endpoint, params in calls if endpoint == "efetch.fcgi"]
    assert fetch_ids and all(re.fullmatch(r"\d+", identifier) for identifier in fetch_ids)
    assert len(fetch_ids) == len(pubmed)
    for source in pubmed:
        check_source(source, run)
        assert source.category == "pubmed"
        assert source.access_level in {"metadata", "abstract"}
        assert source.pmid in fetch_ids

    pubmed_demo = retrieval.retrieve_url("https://pubmed.ncbi.nlm.nih.gov/25484088/", run)[0]
    check_source(pubmed_demo, run)
    assert pubmed_demo.pmid == "25484088"
    assert pubmed_demo.pmcid == DEMO_PMCID
    assert pubmed_demo.access_level == "abstract"

    pmc_full = retrieval.retrieve_url(
        f"https://pmc.ncbi.nlm.nih.gov/articles/{OPEN_FULL_TEXT_PMCID}/", run
    )[0]
    check_source(pmc_full, run)
    assert pmc_full.access_level == "full text"
    assert any(p.location.startswith("XML body paragraph ") for p in pmc_full.passages)

    pmc_demo = retrieval.retrieve_url(
        f"https://pmc.ncbi.nlm.nih.gov/articles/{DEMO_PMCID}/", run
    )[0]
    check_source(pmc_demo, run)
    assert pmc_demo.access_level == "abstract"
    assert not any(p.location.startswith("XML body paragraph ") for p in pmc_demo.passages)

    oai_base = (
        "https://pmc.ncbi.nlm.nih.gov/api/oai/v1/mh/?verb=GetRecord"
        "&identifier=oai:pubmedcentral.nih.gov:4502790&metadataPrefix="
    )
    front_matter, _, _ = fetch(oai_base + "pmc_fm")
    front_root = ET.fromstring(front_matter)
    assert not front_root.findall(".//{*}error")
    oai_full_text_available = False
    oai_full_text_detail = ""
    try:
        full_text, _, _ = fetch(oai_base + "pmc")
        full_root = ET.fromstring(full_text)
        oai_full_text_available = bool(full_root.findall(".//{*}body"))
        oai_full_text_detail = "readable body returned" if oai_full_text_available else "no body returned"
    except FetchError as exc:
        oai_full_text_detail = str(exc)

    product_data, product_url, product_headers = fetch(PRODUCT, allowed_types={"text/html"})
    assert product_url == PRODUCT
    assert MANUAL.encode() in product_data
    product = product_record(product_data, run, product_url, product_headers)
    check_source(product, run)
    assert product.document_version
    assert any("lysosomal function is inhibited" in p.text for p in product.passages)

    manual_data, manual_url, manual_headers = fetch(MANUAL, allowed_types={"application/pdf"})
    assert manual_url == MANUAL
    manual = manual_record(manual_data, run, manual_headers)
    check_source(manual, run)
    assert manual.passages and manual.passages[0].location == "PDF physical page 1"

    print(json.dumps({
        "pubmed_search": {
            "source_count": len(pubmed),
            "individual_fetch_pmids": fetch_ids,
            "access_levels": [source.access_level for source in pubmed],
            "hashes": [source.content_sha256 for source in pubmed],
        },
        "pubmed_demo": {
            "pmid": pubmed_demo.pmid,
            "pmcid": pubmed_demo.pmcid,
            "access_level": pubmed_demo.access_level,
            "hash": pubmed_demo.content_sha256,
        },
        "pmc_full_text": {
            "pmcid": pmc_full.pmcid,
            "access_level": pmc_full.access_level,
            "passage_count": len(pmc_full.passages),
            "first_location": pmc_full.passages[0].location,
            "last_location": pmc_full.passages[-1].location,
            "hash": pmc_full.content_sha256,
        },
        "pmc_demo": {
            "pmcid": pmc_demo.pmcid,
            "access_level": pmc_demo.access_level,
            "passage_count": len(pmc_demo.passages),
            "oai_front_matter_available": True,
            "oai_full_text_available": oai_full_text_available,
            "oai_full_text_detail": oai_full_text_detail,
            "hash": pmc_demo.content_sha256,
        },
        "enzo_product": {
            "document_version": product.document_version,
            "passage_count": len(product.passages),
            "hash": product.content_sha256,
        },
        "enzo_manual": {
            "document_version": manual.document_version,
            "passage_count": len(manual.passages),
            "first_location": manual.passages[0].location,
            "last_location": manual.passages[-1].location,
            "hash": manual.content_sha256,
        },
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

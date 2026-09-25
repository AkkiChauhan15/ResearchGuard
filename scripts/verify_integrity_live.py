"""Bounded read-only verification of PubMed and Crossref notice parsing.

The script performs one PubMed EFetch and one Crossref DOI lookup using their
documented examples. It prints notice metadata only and makes no model call.
"""
from __future__ import annotations

import json

from researchguard.integrity import IntegrityStatus, check_source_integrity
from researchguard.retrieval import retrieve_url
from researchguard.schemas import Source


RETRACTED_PMID = "38510612"
RETRACTION_NOTICE_PMID = "38868598"
CROSSREF_ORIGINAL_DOI = "10.1177/1758835920922055"
CROSSREF_NOTICE_DOI = "10.1177/17588359231172420"


def main() -> None:
    source = retrieve_url(
        f"https://pubmed.ncbi.nlm.nih.gov/{RETRACTED_PMID}/",
        "retrieval_phase_ii_live",
    )[0]
    result = source.integrity
    assert result is not None
    assert result.status == IntegrityStatus.RETRACTED
    assert result.checked_via == "pubmed"
    assert any(
        notice.identifier == f"PMID {RETRACTION_NOTICE_PMID}"
        and notice.relation == "RetractionIn"
        for notice in result.notices
    )
    crossref_source = Source(
        retrieval_run_id="retrieval_phase_ii_live",
        url="https://pmc.ncbi.nlm.nih.gov/articles/PMC1/",
        category="pmc",
        title="Crossref documented retraction example",
        doi=CROSSREF_ORIGINAL_DOI,
        access_level="metadata",
        content_sha256="0" * 64,
        passages=[],
    )
    crossref_result = check_source_integrity(crossref_source)
    assert crossref_result.status == IntegrityStatus.RETRACTED
    assert crossref_result.checked_via == "crossref"
    assert any(
        notice.identifier == f"DOI {CROSSREF_NOTICE_DOI}"
        and notice.relation == "updated-by"
        for notice in crossref_result.notices
    )
    print(json.dumps({
        "pubmed": {
            "source_pmid": source.pmid,
            "source_url": source.url,
            "source_hash": source.content_sha256,
            "integrity_status": result.status,
            "checked_via": result.checked_via,
            "checked_at": result.checked_at,
            "notice_relations": [notice.relation for notice in result.notices],
            "notice_identifiers": [notice.identifier for notice in result.notices],
            "notice_urls": [notice.url for notice in result.notices],
        },
        "crossref": {
            "source_doi": crossref_source.doi,
            "integrity_status": crossref_result.status,
            "checked_via": crossref_result.checked_via,
            "checked_at": crossref_result.checked_at,
            "notice_relations": [notice.relation for notice in crossref_result.notices],
            "notice_identifiers": [notice.identifier for notice in crossref_result.notices],
            "notice_sources": [notice.source for notice in crossref_result.notices],
        },
        "passages_printed": False,
        "model_calls": 0,
    }, indent=2))


if __name__ == "__main__":
    main()

"""Deterministic publication-notice checks for retrieved source records."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
import json
import os
import re
import threading
import time
from typing import TYPE_CHECKING, Literal
from urllib.parse import quote, urlencode
import xml.etree.ElementTree as ET

from pydantic import BaseModel, ConfigDict, Field

from .ncbi import ncbi
from .transport import FetchError, fetch

if TYPE_CHECKING:
    from .schemas import Source


class IntegrityStatus(str, Enum):
    CLEAN = "clean"
    RETRACTED = "retracted"
    CORRECTION = "correction"
    EXPRESSION_OF_CONCERN = "expression_of_concern"
    NOT_APPLICABLE = "not_applicable"
    CHECK_FAILED = "check_failed"


class IntegrityNotice(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["retraction", "correction", "expression_of_concern"]
    relation: str = Field(max_length=120)
    label: str = Field(max_length=1000)
    url: str | None = Field(default=None, max_length=3000)
    identifier: str | None = Field(default=None, max_length=500)
    source: str = Field(max_length=120)


class IntegrityCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: Literal["pubmed", "crossref", "not_applicable", "unavailable"]
    checked_at: str
    outcome: Literal["no_indicators", "notice_found", "not_applicable", "failed"]
    detail: str = Field(max_length=2000)


class IntegrityResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: IntegrityStatus
    checked_at: str
    checked_via: Literal["pubmed", "crossref", "not_applicable", "unavailable"]
    detail: str = Field(max_length=2000)
    notices: list[IntegrityNotice] = Field(default_factory=list, max_length=20)
    checks: list[IntegrityCheck] = Field(default_factory=list, max_length=4)


_crossref_lock = threading.Lock()
_crossref_last_request = 0.0
_DOI = re.compile(r"10\.\d{4,9}/\S+", re.IGNORECASE)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _result(
    status: IntegrityStatus,
    via: Literal["pubmed", "crossref", "not_applicable", "unavailable"],
    detail: str,
    notices: list[IntegrityNotice] | None = None,
    checks: list[IntegrityCheck] | None = None,
) -> IntegrityResult:
    checked_at = _now()
    if status == IntegrityStatus.CLEAN:
        outcome = "no_indicators"
    elif status == IntegrityStatus.NOT_APPLICABLE:
        outcome = "not_applicable"
    elif status == IntegrityStatus.CHECK_FAILED:
        outcome = "failed"
    else:
        outcome = "notice_found"
    return IntegrityResult(
        status=status,
        checked_at=checked_at,
        checked_via=via,
        detail=detail,
        notices=notices or [],
        checks=checks or [IntegrityCheck(method=via, checked_at=checked_at, outcome=outcome, detail=detail)],
    )


def not_applicable_result() -> IntegrityResult:
    return _result(
        IntegrityStatus.NOT_APPLICABLE,
        "not_applicable",
        "Publication-notice checking does not apply to this source type or no PMID/DOI is available.",
    )


def unavailable_result(
    detail: str,
    via: Literal["pubmed", "crossref", "unavailable"] = "unavailable",
) -> IntegrityResult:
    return _result(IntegrityStatus.CHECK_FAILED, via, detail)


def _status(notices: list[IntegrityNotice]) -> IntegrityStatus:
    kinds = {notice.kind for notice in notices}
    if "retraction" in kinds:
        return IntegrityStatus.RETRACTED
    if "expression_of_concern" in kinds:
        return IntegrityStatus.EXPRESSION_OF_CONCERN
    if "correction" in kinds:
        return IntegrityStatus.CORRECTION
    return IntegrityStatus.CLEAN


def _pubmed_kind(ref_type: str) -> Literal["retraction", "correction", "expression_of_concern"] | None:
    normalized = re.sub(r"[^a-z]", "", ref_type.lower())
    if normalized in {"retractionin", "partialretractionin"}:
        return "retraction"
    if normalized == "expressionofconcernin":
        return "expression_of_concern"
    if normalized in {"erratumin", "correctionin", "correctedandrepublishedin", "updatein"}:
        return "correction"
    return None


def integrity_from_pubmed_article(article: ET.Element) -> IntegrityResult:
    """Parse notice relationships from an already fetched PubMed article element."""
    notices: list[IntegrityNotice] = []
    nodes = article.findall("./MedlineCitation/CommentsCorrectionsList/CommentsCorrections")
    nodes.extend(article.findall("./MedlineCitation/CommentsCorrectionList/CommentsCorrections"))
    for node in nodes[:20]:
        ref_type = node.attrib.get("RefType", "")
        kind = _pubmed_kind(ref_type)
        if kind is None:
            continue
        pmid = "".join(node.findtext("PMID", default="").split())
        source_text = " ".join("".join(node.itertext()).split())
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if re.fullmatch(r"\d+", pmid) else None
        notices.append(IntegrityNotice(
            kind=kind,
            relation=ref_type,
            label=source_text[:1000] or ref_type,
            url=url,
            identifier=f"PMID {pmid}" if url else None,
            source="pubmed",
        ))
    status = _status(notices)
    if status == IntegrityStatus.CLEAN:
        detail = "No retraction, correction, or expression-of-concern relations were present in the checked PubMed record."
    else:
        detail = f"PubMed record contained {len(notices)} relevant publication-notice relation(s)."
    return _result(status, "pubmed", detail, notices)


def integrity_from_pubmed_xml(data: bytes, expected_pmid: str) -> IntegrityResult:
    if b"<!ENTITY" in data.upper():
        raise ValueError("PubMed integrity XML contained an unsupported entity declaration.")
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        raise ValueError("PubMed integrity XML could not be parsed.") from None
    for article in root.findall(".//PubmedArticle"):
        pmid = "".join(article.findtext("./MedlineCitation/PMID", default="").split())
        if pmid == expected_pmid:
            return integrity_from_pubmed_article(article)
    raise ValueError(f"PubMed integrity response did not contain requested PMID {expected_pmid}.")


def _crossref_kind(value: object) -> Literal["retraction", "correction", "expression_of_concern"] | None:
    normalized = re.sub(r"[^a-z]", "", str(value).lower())
    if normalized in {"retraction", "partialretraction"}:
        return "retraction"
    if normalized in {"expressionofconcern", "concern"}:
        return "expression_of_concern"
    if normalized in {"correction", "clarification", "erratum", "update"}:
        return "correction"
    return None


def integrity_from_crossref_json(data: bytes, checked_doi: str) -> IntegrityResult:
    try:
        payload = json.loads(data)
        message = payload["message"]
        if not isinstance(message, dict):
            raise TypeError()
    except (json.JSONDecodeError, KeyError, TypeError):
        raise ValueError("Crossref integrity response could not be parsed.") from None
    notices: list[IntegrityNotice] = []
    for field in ("updated-by", "update-to"):
        values = message.get(field, [])
        if values is None:
            values = []
        if not isinstance(values, list):
            raise ValueError("Crossref integrity response contained malformed update metadata.")
        for update in values[:20]:
            if not isinstance(update, dict):
                raise ValueError("Crossref integrity response contained malformed update metadata.")
            kind = _crossref_kind(update.get("type") or update.get("label"))
            if kind is None:
                continue
            doi = str(update.get("DOI") or "").strip()
            safe_doi = doi if _DOI.fullmatch(doi) else None
            source = str(update.get("source") or "crossref")[:120]
            label = str(update.get("label") or update.get("type") or kind)[:1000]
            notices.append(IntegrityNotice(
                kind=kind,
                relation=field,
                label=label,
                url=f"https://doi.org/{quote(safe_doi, safe='/')}" if safe_doi else None,
                identifier=f"DOI {safe_doi}" if safe_doi else None,
                source=f"crossref:{source}",
            ))
    status = _status(notices)
    if status == IntegrityStatus.CLEAN:
        detail = f"No retraction, correction, clarification, or expression-of-concern updates were present in the checked Crossref record for DOI {checked_doi}."
    else:
        detail = f"Crossref record contained {len(notices)} relevant publication-update relation(s)."
    return _result(status, "crossref", detail, notices)


def _crossref(doi: str) -> bytes:
    global _crossref_last_request
    params: dict[str, str] = {}
    contact = (os.getenv("CROSSREF_MAILTO") or os.getenv("NCBI_EMAIL") or "").strip()
    if contact and len(contact) <= 254 and "@" in contact and not any(ord(char) < 33 for char in contact):
        params["mailto"] = contact
    query = "?" + urlencode(params) if params else ""
    url = f"https://api.crossref.org/works/{quote(doi, safe='')}{query}"
    # Single-record public access permits five/second and one concurrent request.
    # Four/second remains below that limit even without a polite-pool contact.
    with _crossref_lock:
        time.sleep(max(0, 0.25 - (time.monotonic() - _crossref_last_request)))
        _crossref_last_request = time.monotonic()
        data, _, _ = fetch(url, allowed_types={"application/json"})
    return data


def _crossref_result(doi: str) -> IntegrityResult:
    try:
        return integrity_from_crossref_json(_crossref(doi), doi)
    except (FetchError, ValueError, TypeError, KeyError, UnicodeError) as exc:
        return unavailable_result(
            f"Crossref integrity check unavailable: {exc}. This source is not confirmed clean.",
            "crossref",
        )


def _complete_after_pubmed(source: "Source", pubmed_result: IntegrityResult) -> IntegrityResult:
    if pubmed_result.status != IntegrityStatus.CLEAN or not source.doi or not _DOI.fullmatch(source.doi):
        return pubmed_result
    crossref_result = _crossref_result(source.doi)
    crossref_result.checks = [*pubmed_result.checks, *crossref_result.checks]
    crossref_result.detail = (
        "The PubMed record had no relevant notice relation. " + crossref_result.detail
    )[:2000]
    return crossref_result


def complete_pubmed_integrity(source: "Source", pubmed_result: IntegrityResult) -> IntegrityResult:
    """Use Crossref only after the supplied PubMed record has no notice hit."""
    return _complete_after_pubmed(source, pubmed_result)


def check_source_integrity(source: "Source") -> IntegrityResult:
    """Check PubMed first, then Crossref when no PMID-level record is available."""
    if source.category in {"manufacturer", "synthetic"}:
        return not_applicable_result()
    if source.pmid and re.fullmatch(r"\d+", source.pmid):
        try:
            data, _, _ = ncbi("efetch.fcgi", {"db": "pubmed", "id": source.pmid, "retmode": "xml"})
            return _complete_after_pubmed(source, integrity_from_pubmed_xml(data, source.pmid))
        except (FetchError, ValueError, TypeError, KeyError, UnicodeError) as exc:
            return unavailable_result(
                f"PubMed integrity check unavailable: {exc}. This source is not confirmed clean.",
                "pubmed",
            )
    if source.doi and _DOI.fullmatch(source.doi):
        return _crossref_result(source.doi)
    return not_applicable_result()

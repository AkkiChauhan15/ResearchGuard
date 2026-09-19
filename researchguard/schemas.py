from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def uid(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


Status = Literal["Supported within the stated context", "Partially supported",
                 "Conflicting evidence", "Contradicted by retrieved evidence",
                 "Insufficient evidence found"]
Access = Literal["ok", "no_results", "partial_access", "rate_limited", "fetch_failed", "parse_failed"]


class Context(Strict):
    organism_model: str = Field(default="", max_length=500)
    assay: str = Field(default="", max_length=500)
    reagent: str = Field(default="", max_length=500)
    conditions: str = Field(default="", max_length=1500)


class ReviewInput(Strict):
    text: str = Field(min_length=1, max_length=12000)
    intended_use: Literal["topic understanding", "assay interpretation", "presentation preparation", "experiment planning"]
    context: Context = Field(default_factory=Context)
    source_urls: list[str] = Field(default_factory=list, max_length=3)


class Passage(Strict):
    text: str
    location: str


class Source(Strict):
    source_id: str = Field(default_factory=lambda: uid("src"))
    retrieval_run_id: str
    url: str
    category: Literal["pubmed", "pmc", "manufacturer", "synthetic"]
    title: str
    authors: list[str] = Field(default_factory=list)
    date: str | None = None
    doi: str | None = None
    pmid: str | None = None
    pmcid: str | None = None
    access_level: Literal["metadata", "abstract", "full text", "product document"]
    retrieved_at: str = Field(default_factory=now)
    document_version: str | None = None
    content_sha256: str
    passages: list[Passage]
    limitations: list[str] = Field(default_factory=list)


class Attempt(Strict):
    retrieval_run_id: str
    claim_id: str
    query_or_url: str
    adapter: str
    access_state: Access
    timestamp: str = Field(default_factory=now)
    detail: str
    source_ids: list[str] = Field(default_factory=list)


class Evidence(Strict):
    source_id: str
    passage: str = Field(min_length=1, max_length=5000)
    location: str
    relationship: Literal["support", "limitation", "conflict"]


class Assessment(Strict):
    status: Status
    evidence: list[Evidence]
    explanation: str
    context_mismatches: list[str]
    limitations: list[str]
    suggested_wording: str
    next_verification_step: str


class Decision(Strict):
    status: Literal["pending", "accepted", "edited", "rejected"] = "pending"
    final_wording: str = Field(default="", max_length=12000)
    notes: str = Field(default="", max_length=5000)


class Claim(Strict):
    claim_id: str = Field(default_factory=lambda: uid("claim"))
    original_span: str
    text: str
    type: Literal["observation", "inference", "mixed", "unclassified"] = "unclassified"
    observations: list[str] = Field(default_factory=list)
    inferences: list[str] = Field(default_factory=list)
    missing_context: list[str] = Field(default_factory=list)
    assessment: Assessment | None = None
    assessment_error: str | None = None
    decision: Decision = Field(default_factory=Decision)


class ModelRun(Strict):
    task: str
    claim_id: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    requested_model: str
    returned_model: str
    prompt_version: str
    timestamp: str = Field(default_factory=now)
    validation: list[str]


class Review(Strict):
    review_id: str = Field(default_factory=lambda: uid("review"))
    created_at: str = Field(default_factory=now)
    mode: Literal["demo", "live"]
    original_input: ReviewInput
    missing_fields: list[str]
    extraction_method: str
    claims: list[Claim]
    attempts: list[Attempt] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    model_runs: list[ModelRun] = Field(default_factory=list)
    validation_results: list[str] = Field(default_factory=list)
    notices: list[str] = Field(default_factory=list)

"""User-scoped Supabase PostgREST persistence for canonical review records."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any
from uuid import UUID

import httpx
from pydantic import ValidationError

from .export import validate_review
from .schemas import Review


SAVED_REVIEW_SCHEMA_VERSION = 1
ROW_COLUMNS = "id,review_id,schema_version,revision,mode,title,created_at,updated_at,record"
SUMMARY_COLUMNS = "id,review_id,schema_version,revision,mode,title,created_at,updated_at"
REVIEW_ID_PATTERN = re.compile(r"review_[0-9a-f]{32}")


class PersistenceUnavailable(RuntimeError):
    pass


class PersistenceConflict(RuntimeError):
    pass


class PersistenceNotFound(LookupError):
    pass


class PersistencePermissionDenied(RuntimeError):
    pass


@dataclass(frozen=True)
class SavedReviewSummary:
    saved_id: str
    review_id: str
    schema_version: int
    revision: int
    mode: str
    title: str
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "saved_id": self.saved_id,
            "review_id": self.review_id,
            "schema_version": self.schema_version,
            "revision": self.revision,
            "mode": self.mode,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass(frozen=True)
class SavedReviewRecord:
    summary: SavedReviewSummary
    review: Review

    def as_dict(self) -> dict[str, Any]:
        return {**self.summary.as_dict(), "review": self.review.model_dump(mode="json")}


def _title(review: Review) -> str:
    text = review.claims[0].text if review.claims else review.original_input.text
    return " ".join(text.split())[:300] or "Untitled review"


def _summary(row: dict[str, Any]) -> SavedReviewSummary:
    try:
        saved_id = str(UUID(str(row["id"])))
        review_id = str(row["review_id"])
        schema_version = int(row["schema_version"])
        revision = int(row["revision"])
        mode = str(row["mode"])
        title = str(row["title"])
        created_at = str(row["created_at"])
        updated_at = str(row["updated_at"])
    except (KeyError, TypeError, ValueError):
        raise PersistenceUnavailable("Saved-review service returned malformed metadata.") from None
    if (
        schema_version != SAVED_REVIEW_SCHEMA_VERSION
        or revision < 1
        or mode not in {"demo", "live"}
        or not REVIEW_ID_PATTERN.fullmatch(review_id)
        or not 1 <= len(title) <= 300
    ):
        raise PersistenceUnavailable("Saved-review service returned unsupported metadata.")
    return SavedReviewSummary(
        saved_id=saved_id,
        review_id=review_id,
        schema_version=schema_version,
        revision=revision,
        mode=mode,
        title=title,
        created_at=created_at,
        updated_at=updated_at,
    )


def _record(row: dict[str, Any]) -> SavedReviewRecord:
    summary = _summary(row)
    try:
        review = Review.model_validate(row["record"])
        validate_review(review)
    except (KeyError, ValidationError, ValueError):
        raise PersistenceUnavailable("Saved review failed canonical schema or evidence validation.") from None
    if review.review_id != summary.review_id or review.mode != summary.mode:
        raise PersistenceUnavailable("Saved review metadata does not match its canonical record.")
    return SavedReviewRecord(summary=summary, review=review)


class SupabaseReviewRepository:
    """Call PostgREST with the user's JWT so database RLS remains authoritative."""

    def __init__(
        self,
        project_url: str | None,
        publishable_key: str | None,
        *,
        timeout_seconds: float = 10,
        client: httpx.AsyncClient | None = None,
    ):
        self.project_url = project_url.rstrip("/") if project_url else None
        self.publishable_key = publishable_key.strip() if publishable_key else None
        self.configured = bool(self.project_url and self.publishable_key)
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            base_url=self.project_url or "https://unconfigured.invalid",
            timeout=httpx.Timeout(timeout_seconds),
            follow_redirects=False,
            limits=httpx.Limits(max_connections=4, max_keepalive_connections=2),
            headers={"User-Agent": "ResearchGuardAI/0.5 local-persistence"},
        )

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    def _headers(self, access_token: str, *, write: bool = False) -> dict[str, str]:
        if not self.configured:
            raise PersistenceUnavailable(
                "Saved reviews are unavailable: configure SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY."
            )
        headers = {
            "apikey": self.publishable_key or "",
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
        }
        if write:
            headers.update({"Content-Type": "application/json", "Prefer": "return=representation"})
        return headers

    @staticmethod
    async def _payload(response: httpx.Response) -> list[dict[str, Any]]:
        if response.status_code in {401, 403}:
            raise PersistencePermissionDenied("Saved-review access was denied by authentication or row-level security.")
        if response.status_code == 409:
            raise PersistenceConflict("This review already has a saved record. Open it and use Update saved copy.")
        if response.status_code >= 500:
            raise PersistenceUnavailable("Saved-review service is temporarily unavailable. Your local review was kept.")
        if response.status_code >= 400:
            raise PersistenceUnavailable("Saved-review request failed. Your local review was kept.")
        try:
            payload = response.json()
        except ValueError:
            raise PersistenceUnavailable("Saved-review service returned malformed JSON.") from None
        if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
            raise PersistenceUnavailable("Saved-review service returned an unexpected response.")
        return payload

    async def list(self, access_token: str) -> list[SavedReviewSummary]:
        try:
            response = await self.client.get(
                "/rest/v1/saved_reviews",
                params={"select": SUMMARY_COLUMNS, "order": "updated_at.desc", "limit": "100"},
                headers=self._headers(access_token),
            )
        except httpx.HTTPError:
            raise PersistenceUnavailable("Saved-review service is unreachable. Your local review was kept.") from None
        return [_summary(row) for row in await self._payload(response)]

    async def get(self, access_token: str, saved_id: str) -> SavedReviewRecord:
        try:
            response = await self.client.get(
                "/rest/v1/saved_reviews",
                params={"id": f"eq.{saved_id}", "select": ROW_COLUMNS, "limit": "1"},
                headers=self._headers(access_token),
            )
        except httpx.HTTPError:
            raise PersistenceUnavailable("Saved-review service is unreachable. Your local review was kept.") from None
        rows = await self._payload(response)
        if not rows:
            raise PersistenceNotFound("Saved review not found, or it belongs to another user.")
        return _record(rows[0])

    async def create(self, access_token: str, review: Review) -> SavedReviewRecord:
        validate_review(review)
        body = {
            "review_id": review.review_id,
            "schema_version": SAVED_REVIEW_SCHEMA_VERSION,
            "mode": review.mode,
            "title": _title(review),
            "record": review.model_dump(mode="json"),
        }
        try:
            response = await self.client.post(
                "/rest/v1/saved_reviews",
                params={"select": ROW_COLUMNS},
                headers=self._headers(access_token, write=True),
                json=body,
            )
        except httpx.HTTPError:
            raise PersistenceUnavailable("Saved-review service is unreachable. Your local review was kept.") from None
        rows = await self._payload(response)
        if len(rows) != 1:
            raise PersistenceUnavailable("Saved-review service did not confirm the new record.")
        return _record(rows[0])

    async def update(
        self,
        access_token: str,
        saved_id: str,
        expected_revision: int,
        review: Review,
    ) -> SavedReviewRecord:
        validate_review(review)
        body = {
            "title": _title(review),
            "record": review.model_dump(mode="json"),
        }
        try:
            response = await self.client.patch(
                "/rest/v1/saved_reviews",
                params={
                    "id": f"eq.{saved_id}",
                    "revision": f"eq.{expected_revision}",
                    "select": ROW_COLUMNS,
                },
                headers=self._headers(access_token, write=True),
                json=body,
            )
        except httpx.HTTPError:
            raise PersistenceUnavailable("Saved-review service is unreachable. Your local review was kept.") from None
        rows = await self._payload(response)
        if not rows:
            try:
                await self.get(access_token, saved_id)
            except PersistenceNotFound:
                raise
            raise PersistenceConflict(
                "The saved review changed elsewhere. Your local review was kept; reopen the saved copy before updating."
            )
        if len(rows) != 1:
            raise PersistenceUnavailable("Saved-review service returned an unexpected update result.")
        return _record(rows[0])

    async def delete(self, access_token: str, saved_id: str, expected_revision: int) -> SavedReviewSummary:
        try:
            response = await self.client.delete(
                "/rest/v1/saved_reviews",
                params={
                    "id": f"eq.{saved_id}",
                    "revision": f"eq.{expected_revision}",
                    "select": SUMMARY_COLUMNS,
                },
                headers=self._headers(access_token, write=True),
            )
        except httpx.HTTPError:
            raise PersistenceUnavailable("Saved-review service is unreachable. No local review was removed.") from None
        rows = await self._payload(response)
        if not rows:
            try:
                await self.get(access_token, saved_id)
            except PersistenceNotFound:
                raise
            raise PersistenceConflict("The saved review changed elsewhere. Refresh the list before deleting it.")
        if len(rows) != 1:
            raise PersistenceUnavailable("Saved-review service returned an unexpected delete result.")
        return _summary(rows[0])

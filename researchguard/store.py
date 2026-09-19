"""Process-local, expiring storage for unsaved review drafts."""
import asyncio
from dataclasses import dataclass
import time
from typing import Callable

from .schemas import Review


NOT_FOUND = "Review not found in this session, or expired. Start a new review."


@dataclass
class ReviewEntry:
    created_monotonic: float
    session_id: str
    review: Review
    lock: asyncio.Lock
    owner_id: str | None = None


class ReviewStore:
    def __init__(self, ttl_seconds: int, max_reviews: int, clock: Callable[[], float] = time.monotonic):
        self.ttl_seconds = ttl_seconds
        self.max_reviews = max_reviews
        self.clock = clock
        self.items: dict[str, ReviewEntry] = {}
        self.lock = asyncio.Lock()

    def _prune_locked(self) -> None:
        current = self.clock()
        for review_id, entry in list(self.items.items()):
            if current - entry.created_monotonic > self.ttl_seconds:
                del self.items[review_id]

    async def prune(self) -> None:
        async with self.lock:
            self._prune_locked()

    async def add(self, session_id: str, review: Review, owner_id: str | None = None) -> None:
        async with self.lock:
            self._prune_locked()
            if len(self.items) >= self.max_reviews:
                raise ValueError("Local review capacity reached; restart the preview or wait for expiry.")
            self.items[review.review_id] = ReviewEntry(
                created_monotonic=self.clock(),
                session_id=session_id,
                review=review,
                lock=asyncio.Lock(),
                owner_id=owner_id,
            )

    async def get_session_entry(self, session_id: str, review_id: str) -> ReviewEntry:
        async with self.lock:
            self._prune_locked()
            entry = self.items.get(review_id)
            if entry is None or entry.session_id != session_id:
                raise LookupError(NOT_FOUND)
            return entry

    async def get_entry(self, session_id: str, review_id: str, owner_id: str | None = None) -> ReviewEntry:
        entry = await self.get_session_entry(session_id, review_id)
        async with self.lock:
            self._prune_locked()
            if self.items.get(review_id) is not entry:
                raise LookupError(NOT_FOUND)
            if entry.owner_id is not None and entry.owner_id != owner_id:
                raise LookupError(NOT_FOUND)
            return entry

    async def snapshot(self, session_id: str, review_id: str, owner_id: str | None = None) -> Review:
        entry = await self.get_entry(session_id, review_id, owner_id)
        async with entry.lock:
            current = await self.get_entry(session_id, review_id, owner_id)
            if current is not entry:
                raise LookupError(NOT_FOUND)
            return entry.review.model_copy(deep=True)

    async def commit(self, session_id: str, review_id: str, entry: ReviewEntry, review: Review, owner_id: str | None = None) -> None:
        async with self.lock:
            self._prune_locked()
            current = self.items.get(review_id)
            if current is not entry or current.session_id != session_id or current.owner_id != owner_id:
                raise LookupError("Review expired while processing. Start a new review.")
            current.review = review

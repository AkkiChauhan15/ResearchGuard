"""Small process-local per-user limiter for the authenticated chat route."""
from __future__ import annotations

import asyncio
from collections import defaultdict, deque
import time


class ChatRateLimiter:
    def __init__(self, requests_per_minute: int):
        self.limit = requests_per_minute
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, user_id: str) -> int | None:
        now = time.monotonic()
        async with self._lock:
            events = self._events[user_id]
            while events and now - events[0] >= 60:
                events.popleft()
            if len(events) >= self.limit:
                return max(1, int(60 - (now - events[0])))
            events.append(now)
            if not events:
                self._events.pop(user_id, None)
            return None

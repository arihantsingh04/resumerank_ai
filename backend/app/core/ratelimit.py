"""Small in-memory sliding-window rate limiter (single-process deployment, D-28)."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

from app.core.errors import RateLimited


class RateLimiter:
    def __init__(
        self,
        max_calls: int,
        window_s: float,
        clock: Callable[[], float] = time.monotonic,
        max_keys: int = 10_000,
    ) -> None:
        self.max_calls = max_calls
        self.window_s = window_s
        self.max_keys = max_keys
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, now: float) -> None:
        stale = [k for k, h in self._hits.items() if not h or now - h[-1] > self.window_s]
        for k in stale:
            del self._hits[k]

    def check(self, key: str) -> None:
        now = self._clock()
        with self._lock:
            if len(self._hits) >= self.max_keys:
                self._prune(now)  # bounded memory even if keys are spoofed
            hits = self._hits[key]
            while hits and now - hits[0] > self.window_s:
                hits.popleft()
            if len(hits) >= self.max_calls:
                raise RateLimited("Too many attempts. Wait a minute and try again.")
            hits.append(now)

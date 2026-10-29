"""Daily AI budgets without accounts (D-36): a per-IP cap and a global cap, both in memory.

Single-instance state; move to Redis when running several API instances (DESIGN §10).
"""

from __future__ import annotations

import datetime as dt
import threading
from collections import defaultdict
from collections.abc import Callable


def _utc_today() -> dt.date:
    return dt.datetime.now(dt.UTC).date()


class AIBudget:
    def __init__(self, per_ip: int, global_daily: int, today: Callable[[], dt.date] = _utc_today) -> None:
        self.per_ip = per_ip
        self.global_daily = global_daily
        self._today = today
        self._day: dt.date | None = None
        self._by_ip: dict[str, int] = defaultdict(int)
        self._total = 0
        self._lock = threading.Lock()

    def _roll(self) -> None:
        today = self._today()
        if today != self._day:
            self._day, self._by_ip, self._total = today, defaultdict(int), 0

    def try_acquire(self, ip: str, n: int = 1) -> bool:
        """Reserve `n` AI calls for `ip` today. Returns False (reserving nothing) if a cap would be passed."""
        with self._lock:
            self._roll()
            if self._by_ip[ip] + n > self.per_ip or self._total + n > self.global_daily:
                return False
            self._by_ip[ip] += n
            self._total += n
            return True

    def refund(self, ip: str, n: int = 1) -> None:
        """Give back calls that never reached Gemini (e.g. the call failed before being billed)."""
        with self._lock:
            self._roll()
            self._by_ip[ip] = max(0, self._by_ip[ip] - n)
            self._total = max(0, self._total - n)

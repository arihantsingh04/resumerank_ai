"""Composition root: builds every long-lived object once. Tests pass fakes (encoder, llm)."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any

from app.core.config import Settings
from app.core.ratelimit import RateLimiter
from app.services.ai_budget import AIBudget
from app.services.embeddings.encoder import Encoder, build_encoder
from app.services.llm.client import LLMClient, build_llm

_DEFAULT: Any = object()


@dataclass
class Container:
    settings: Settings
    encoder: Encoder
    llm: LLMClient | None
    check_limiter: RateLimiter
    ai_budget: AIBudget
    slots: threading.BoundedSemaphore  # max concurrent checks (D-36)
    _services: dict[str, Any] = field(default_factory=dict)

    @property
    def checker(self):
        from app.services.checker import Checker

        if "checker" not in self._services:
            self._services["checker"] = Checker(self)
        return self._services["checker"]


def build_container(
    settings: Settings, *, encoder: Encoder | None = None, llm: LLMClient | None = _DEFAULT
) -> Container:
    return Container(
        settings=settings,
        encoder=encoder or build_encoder(settings),
        llm=build_llm(settings) if llm is _DEFAULT else llm,
        check_limiter=RateLimiter(max_calls=settings.checks_per_minute_per_ip, window_s=60),
        ai_budget=AIBudget(
            per_ip=settings.ai_checks_per_ip_per_day, global_daily=settings.gemini_daily_budget
        ),
        slots=threading.BoundedSemaphore(settings.max_concurrent_checks),
    )

"""Gemini adapter (D-05, D-11, D-12).

Every call: rate-limited client-side, retried with backoff on transient errors, forced into a JSON
schema, and validated with Pydantic before anything downstream sees it.
"""

from __future__ import annotations

import datetime as dt
import logging
import threading
import time
from collections.abc import Callable
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.services.llm import prompts
from app.services.llm.schemas import Coaching, JobRequirements

log = logging.getLogger(__name__)
M = TypeVar("M", bound=BaseModel)

MAX_RESUME_CHARS = 24_000
MAX_ATTEMPTS = 2
MAX_JD_CHARS = 20_000


class LLMError(Exception):
    """The LLM call failed or returned unusable output."""


class LLMQuotaExceeded(LLMError):
    """The Gemini key's daily quota is used up. Retrying today won't help."""


class _Transient(Exception):
    pass


class LLMClient(Protocol):
    def extract_requirements(self, jd: str) -> JobRequirements: ...

    def coach(self, req: JobRequirements, job_title: str, resume_text: str, signals: dict) -> Coaching: ...


class RpmLimiter:
    """Spaces calls evenly so at most `rpm` start per minute across all threads."""

    def __init__(
        self,
        rpm: int,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.interval = 60.0 / rpm
        self._clock = clock
        self._sleep = sleep
        self._next = 0.0
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = self._clock()
            wait = max(0.0, self._next - now)
            self._next = max(now, self._next) + self.interval
        if wait > 0:
            self._sleep(wait)


def _classify(exc: Exception) -> Exception:
    """Map SDK/network errors onto our error types."""
    code = getattr(exc, "code", None)
    message = str(getattr(exc, "message", "") or exc)
    if code == 429:
        # google-genai keeps the quotaId (e.g. "...PerDayPerProject...") in the details, which only
        # str(exc) includes, not in `.message`.
        low = f"{message} {exc} {getattr(exc, 'details', '')}".lower()
        if "perday" in low or "per day" in low or "daily" in low:
            return LLMQuotaExceeded("Gemini daily quota exceeded.")
        return _Transient(message)
    if isinstance(code, int) and (code >= 500 or code == 408):
        return _Transient(message)
    if isinstance(exc, TimeoutError | ConnectionError) or type(exc).__name__ in {
        "TimeoutException",
        "ConnectError",
        "ReadTimeout",
        "RemoteProtocolError",
    }:
        return _Transient(message)
    return LLMError(f"Gemini request failed ({code or type(exc).__name__}).")


class GeminiLLM:
    def __init__(self, settings: Settings, genai_client=None, retry_wait: float | None = None) -> None:
        self.settings = settings
        if genai_client is None:
            from google import genai
            from google.genai import types

            genai_client = genai.Client(
                api_key=settings.gemini_api_key,
                http_options=types.HttpOptions(timeout=settings.gemini_timeout_s * 1000),
            )
        self._client = genai_client
        self._limiter = RpmLimiter(settings.gemini_rpm)
        self._retry_wait = 1.0 if retry_wait is None else retry_wait
        self._sleep = time.sleep
        self._paused_until: dt.datetime | None = None

    def _check_paused(self) -> None:
        if self._paused_until and dt.datetime.now(dt.UTC) < self._paused_until:
            raise LLMQuotaExceeded("Gemini daily quota exceeded; paused until it resets.")

    def _pause_for_today(self) -> None:
        """Daily quotas reset at midnight Pacific time; pausing until the next 08:00 UTC covers it."""
        now = dt.datetime.now(dt.UTC)
        resume = now.replace(hour=8, minute=0, second=0, microsecond=0)
        if resume <= now:
            resume += dt.timedelta(days=1)
        self._paused_until = resume
        log.warning("Gemini daily quota exhausted; AI calls paused until %s", resume.isoformat())

    def _generate(self, *, models: list[str], system: str, contents: str, schema: type[M]) -> M:
        """At most MAX_ATTEMPTS calls: attempt i uses models[i] (or the last model).

        Overloaded / timed-out models aren't retried in a loop: a busy primary model falls straight
        through to the fallback (D-11).
        """
        from google.genai import types

        self._check_paused()
        config = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            response_json_schema=schema.model_json_schema(),
            temperature=0.1,
        )
        last: Exception | None = None
        for attempt in range(MAX_ATTEMPTS):
            model = models[min(attempt, len(models) - 1)]
            if attempt and model == models[min(attempt - 1, len(models) - 1)]:
                self._sleep(self._retry_wait)  # same model again: brief pause; different model: go now
            self._limiter.acquire()
            try:
                resp = self._client.models.generate_content(model=model, contents=contents, config=config)
            except Exception as e:
                err = _classify(e)
                if isinstance(err, LLMQuotaExceeded):
                    self._pause_for_today()
                    raise err from e
                if not isinstance(err, _Transient):
                    raise err from e
                log.info(
                    "Gemini %s unavailable (%s); %s",
                    model,
                    getattr(e, "code", type(e).__name__),
                    "trying fallback" if attempt + 1 < MAX_ATTEMPTS else "giving up",
                )
                last = e
                continue
            if not getattr(resp, "text", None):
                raise LLMError("Gemini returned an empty response.")
            try:
                return schema.model_validate_json(resp.text)
            except ValidationError as e:
                log.warning("Gemini output failed %s validation", schema.__name__)
                raise LLMError("Gemini returned output in an unexpected format.") from e
        raise LLMError("Gemini is busy right now. Try again shortly.") from last

    def extract_requirements(self, jd: str) -> JobRequirements:
        return self._generate(
            models=[self.settings.gemini_parse_model],
            system=prompts.REQUIREMENTS_SYSTEM,
            contents=prompts.requirements_prompt(jd[:MAX_JD_CHARS]),
            schema=JobRequirements,
        )

    def coach(self, req: JobRequirements, job_title: str, resume_text: str, signals: dict) -> Coaching:
        return self._generate(
            models=[self.settings.gemini_rerank_model, self.settings.gemini_fallback_model],
            system=prompts.COACH_SYSTEM,
            contents=prompts.coach_prompt(
                job_title, req.model_dump(), signals, resume_text[:MAX_RESUME_CHARS]
            ),
            schema=Coaching,
        )


def build_llm(settings: Settings) -> LLMClient | None:
    return GeminiLLM(settings) if settings.gemini_enabled else None

"""JD text → structured requirements (D-37): Gemini when available and in budget, else the catalogue."""

from __future__ import annotations

import hashlib
import logging
import threading
from collections import OrderedDict
from typing import Literal

from app.services.ai_budget import AIBudget
from app.services.llm.client import LLMClient, LLMError
from app.services.llm.schemas import JobRequirements
from app.services.scoring.skill_catalog import extract_min_years, extract_skills

log = logging.getLogger(__name__)
Source = Literal["ai", "catalog"]
CACHE_SIZE = 256
MIN_CATALOG_SKILLS = 3


class RequirementsService:
    def __init__(self, llm: LLMClient | None, budget: AIBudget) -> None:
        self.llm = llm
        self.budget = budget
        self._cache: OrderedDict[str, JobRequirements] = OrderedDict()
        self._lock = threading.Lock()

    @staticmethod
    def from_catalog(jd: str) -> JobRequirements:
        required, nice = extract_skills(jd)
        return JobRequirements(
            required_skills=required, nice_to_have_skills=nice, min_years_experience=extract_min_years(jd)
        )

    def for_text(self, jd: str, ip: str) -> tuple[JobRequirements, Source]:
        """Catalogue first (instant, free). Gemini only when the catalogue finds too few skills to judge."""
        catalog = self.from_catalog(jd)
        if len(catalog.required_skills) + len(catalog.nice_to_have_skills) >= MIN_CATALOG_SKILLS:
            return catalog, "catalog"
        key = hashlib.sha256(jd.encode()).hexdigest()
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                return self._cache[key], "ai"
        if self.llm is not None and self.budget.try_acquire(ip):
            try:
                reqs = self.llm.extract_requirements(jd)
            except LLMError as e:
                log.info("requirement extraction fell back to catalogue: %s", type(e).__name__)
                self.budget.refund(ip)
            else:
                if reqs.required_skills or reqs.nice_to_have_skills:
                    with self._lock:
                        self._cache[key] = reqs
                        if len(self._cache) > CACHE_SIZE:
                            self._cache.popitem(last=False)
                    return reqs, "ai"
        return catalog, "catalog"

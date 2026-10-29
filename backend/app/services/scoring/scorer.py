"""Stage-1 scoring: pure functions, no I/O (DESIGN §3.3)."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class Weights(BaseModel):
    semantic: float = Field(0.40, ge=0, le=1)
    skills: float = Field(0.45, ge=0, le=1)
    experience: float = Field(0.15, ge=0, le=1)

    @model_validator(mode="after")
    def _sum_to_one(self) -> Weights:
        if abs(self.semantic + self.skills + self.experience - 1) > 0.001:
            raise ValueError("weights must add up to 1")
        return self


class SkillMatch(BaseModel):
    requirement: str
    required: bool
    matched: bool
    source: Literal["parsed", "keyword", "semantic"] | None = None
    evidence: str | None = None
    similarity: float | None = None


def calibrate(sim: float, low: float, high: float) -> float:
    return max(0.0, min(100.0, (sim - low) / (high - low) * 100))


def experience_score(years: float | None, min_years: float | None) -> float:
    if not min_years:
        return 100.0
    if years is None:
        return 50.0
    return min(years / min_years, 1.0) * 100


def skill_coverage(matches: list[SkillMatch]) -> float:
    if not matches:
        return 50.0
    total = sum(2 if m.required else 1 for m in matches)
    got = sum(2 if m.required else 1 for m in matches if m.matched)
    return got / total * 100


def stage1(semantic: float, skills: float, experience: float, w: Weights) -> float:
    return w.semantic * semantic + w.skills * skills + w.experience * experience


def blend(stage1_score: float, llm_score: float | None, llm_weight: float) -> float:
    if llm_score is None:
        return stage1_score
    return (1 - llm_weight) * stage1_score + llm_weight * llm_score


_YEARS = re.compile(r"(\d{1,2}(?:\.\d)?)\s*\+?\s*(?:years|yrs)\b", re.IGNORECASE)


def estimate_years(text: str) -> float | None:
    """Fallback when Gemini parsing is unavailable: the largest 'N years' statement."""
    vals = [float(v) for v in _YEARS.findall(text) if 0 < float(v) <= 50]
    return max(vals) if vals else None


_HEADING_PREFIX = re.compile(r"^(?:[A-Z][A-Z &/]{3,}\s+)+")
_SENTENCE = re.compile(r"(?<=[.!?;])\s+|\s+\|\s+")


def excerpt(chunk: str, requirement: str, max_chars: int = 280) -> str:
    """The sentence of `chunk` that best supports `requirement`."""
    words = {w for w in re.findall(r"\w+", requirement.lower()) if len(w) > 1}
    sentences = [s.strip() for s in _SENTENCE.split(chunk) if s.strip()] or [chunk]
    best = max(sentences, key=lambda s: len(words & set(re.findall(r"\w+", s.lower()))))
    best = _HEADING_PREFIX.sub("", best) or best  # drop a section heading glued to the sentence
    return best if len(best) <= max_chars else best[: max_chars - 1].rstrip() + "…"

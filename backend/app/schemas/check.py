"""Report returned by POST /check (DESIGN §5)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from app.services.health import HealthCheck
from app.services.llm.schemas import BulletRewrite, Suggestion


class SkillResult(BaseModel):
    requirement: str
    required: bool
    source: Literal["keyword", "semantic"] | None = None
    evidence: str | None = None
    similarity: float | None = None
    tip: str | None = None


class Breakdown(BaseModel):
    semantic: float
    skills: float
    experience: float
    ai: float | None = None


class JobInfo(BaseModel):
    title: str
    source: Literal["template", "file", "text"]
    template_id: str | None = None


class AIReport(BaseModel):
    status: Literal["ok", "disabled", "limited", "error"]
    summary: str | None = None
    strengths: list[str] = []
    gaps: list[str] = []
    suggestions: list[Suggestion] = []
    keywords_to_add: list[str] = []
    bullet_rewrites: list[BulletRewrite] = []


class Meta(BaseModel):
    resume_words: int
    ms: int
    requirements_source: Literal["template", "ai", "catalog"]


class Report(BaseModel):
    score: float
    verdict: Literal["strong", "good", "fair", "low"]
    breakdown: Breakdown
    job: JobInfo
    matched: list[SkillResult]
    missing: list[SkillResult]
    years_experience: float | None
    min_years: float | None
    health: list[HealthCheck]
    tips: list[str]
    ai: AIReport
    meta: Meta


class TemplateSummary(BaseModel):
    id: str
    title: str
    category: str
    icon: str
    summary: str
    seniority: str
    required_skills: list[str]
    nice_to_have_skills: list[str]


class TemplateDetail(TemplateSummary):
    description: str

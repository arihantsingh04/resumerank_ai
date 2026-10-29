"""Structured outputs the LLM must return. Validated and clamped with Pydantic (D-05, D-12)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


def _clean_list(v: object, max_items: int, max_len: int = 200) -> list[str]:
    if not isinstance(v, list):
        return []
    out: list[str] = []
    for item in v:
        s = str(item).strip()[:max_len]
        if s and s.lower() not in {x.lower() for x in out}:
            out.append(s)
    return out[:max_items]


def _years(v: object) -> float | None:
    try:
        f = float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return f if 0 <= f <= 60 else None


class JobRequirements(BaseModel):
    required_skills: list[str] = Field(
        default_factory=list, description="Must-have skills, short canonical names"
    )
    nice_to_have_skills: list[str] = Field(default_factory=list, description="Preferred / bonus skills")
    min_years_experience: float | None = Field(default=None, description="Minimum years of experience")
    education: str | None = Field(default=None, description="Education requirement, if any")
    responsibilities: list[str] = Field(default_factory=list, description="Key duties of the role")

    @field_validator("required_skills", "nice_to_have_skills", mode="before")
    @classmethod
    def _skills(cls, v: object) -> list[str]:
        return _clean_list(v, 30, 60)

    @field_validator("responsibilities", mode="before")
    @classmethod
    def _resp(cls, v: object) -> list[str]:
        return _clean_list(v, 15, 300)

    @field_validator("min_years_experience", mode="before")
    @classmethod
    def _min_years(cls, v: object) -> float | None:
        return _years(v)

    @field_validator("education", mode="before")
    @classmethod
    def _edu(cls, v: object) -> str | None:
        s = str(v).strip()[:300] if v else ""
        return s or None


class Suggestion(BaseModel):
    title: str = Field(description="Short imperative headline, e.g. 'Quantify your API project'")
    detail: str = Field(description="One or two sentences of specific advice")

    @field_validator("title", mode="before")
    @classmethod
    def _t(cls, v: object) -> str:
        return str(v or "").strip()[:80]

    @field_validator("detail", mode="before")
    @classmethod
    def _d(cls, v: object) -> str:
        return str(v or "").strip()[:300]


class BulletRewrite(BaseModel):
    before: str = Field(description="A weak line quoted from the resume")
    after: str = Field(description="Stronger rewrite using only facts present in the resume")

    @field_validator("before", "after", mode="before")
    @classmethod
    def _s(cls, v: object) -> str:
        return str(v or "").strip()[:300]


class Coaching(BaseModel):
    llm_score: int = Field(description="0-100 fit of this resume for the role")
    summary: str = Field(description="Two-sentence honest verdict addressed to the candidate")
    strengths: list[str] = Field(default_factory=list, description="Up to 5 strengths relevant to the job")
    gaps: list[str] = Field(default_factory=list, description="Up to 5 gaps versus the job")
    suggestions: list[Suggestion] = Field(default_factory=list, description="Up to 6 concrete improvements")
    keywords_to_add: list[str] = Field(
        default_factory=list, description="Up to 10 JD keywords worth adding if true"
    )
    bullet_rewrites: list[BulletRewrite] = Field(default_factory=list, description="Up to 3 bullet rewrites")

    @field_validator("llm_score", mode="before")
    @classmethod
    def _clamp(cls, v: object) -> int:
        try:
            return max(0, min(100, round(float(v))))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return 0

    @field_validator("summary", mode="before")
    @classmethod
    def _summary(cls, v: object) -> str:
        return str(v or "").strip()[:600]

    @field_validator("strengths", "gaps", mode="before")
    @classmethod
    def _lists(cls, v: object) -> list[str]:
        return _clean_list(v, 5, 300)

    @field_validator("keywords_to_add", mode="before")
    @classmethod
    def _kw(cls, v: object) -> list[str]:
        return _clean_list(v, 10, 60)

    @field_validator("suggestions", mode="before")
    @classmethod
    def _sugg(cls, v: object) -> object:
        return v[:6] if isinstance(v, list) else []

    @field_validator("bullet_rewrites", mode="before")
    @classmethod
    def _rw(cls, v: object) -> object:
        if not isinstance(v, list):
            return []
        seen, out = set(), []
        for item in v:
            key = str(item.get("before", "") if isinstance(item, dict) else item)
            if key not in seen:
                seen.add(key)
                out.append(item)
        return out[:3]

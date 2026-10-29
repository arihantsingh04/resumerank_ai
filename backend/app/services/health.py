"""Deterministic resume health checks (D-39). Instant, free and explainable."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel

Status = Literal["pass", "warn", "fail"]


class HealthCheck(BaseModel):
    id: str
    label: str
    status: Status
    detail: str


ACTION_VERBS = {
    "built",
    "developed",
    "designed",
    "implemented",
    "led",
    "created",
    "optimized",
    "optimised",
    "improved",
    "reduced",
    "increased",
    "automated",
    "deployed",
    "launched",
    "architected",
    "engineered",
    "migrated",
    "integrated",
    "delivered",
    "analyzed",
    "analysed",
    "researched",
    "mentored",
    "shipped",
    "tested",
    "refactored",
    "scaled",
    "configured",
    "trained",
    "won",
    "achieved",
    "established",
    "streamlined",
}
WEAK_PHRASES = ("responsible for", "worked on", "helped with", "helped the", "duties included", "involved in")
_SECTIONS = {
    "experience or projects": ("experience", "internship", "projects", "employment", "work history"),
    "education": ("education", "academic", "qualification"),
    "skills": ("skills", "technologies", "tech stack", "tools"),
}
_NUMBER = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:%|x\b|k\b|\+|ms\b|users|requests|downloads|people|members)?", re.I
)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+|•|•", text) if len(s.strip()) > 15]


def run_checks(text: str, contact: dict[str, list[str]]) -> list[HealthCheck]:
    words = len(text.split())
    low = text.lower()
    sentences = _sentences(text)
    out: list[HealthCheck] = []

    if words < 250:
        out.append(
            HealthCheck(
                id="length",
                label="Length",
                status="warn",
                detail=f"{words} words. That's thin; aim for 350–800 words on one page.",
            )
        )
    elif words > 1100:
        out.append(
            HealthCheck(
                id="length",
                label="Length",
                status="warn",
                detail=f"{words} words. Trim to the most relevant work; 1–2 pages max.",
            )
        )
    else:
        out.append(
            HealthCheck(id="length", label="Length", status="pass", detail=f"{words} words. A good length.")
        )

    has_email, has_phone = bool(contact.get("emails")), bool(contact.get("phones"))
    if has_email and has_phone:
        out.append(
            HealthCheck(id="contact", label="Contact details", status="pass", detail="Email and phone found.")
        )
    else:
        missing = " and ".join(x for x, ok in (("email", has_email), ("phone number", has_phone)) if not ok)
        out.append(
            HealthCheck(
                id="contact",
                label="Contact details",
                status="fail" if not has_email else "warn",
                detail=f"No {missing} found. Recruiters need a way to reach you.",
            )
        )

    missing_sections = [name for name, keys in _SECTIONS.items() if not any(k in low for k in keys)]
    out.append(
        HealthCheck(
            id="sections",
            label="Key sections",
            status="pass" if not missing_sections else ("warn" if len(missing_sections) == 1 else "fail"),
            detail="Experience/projects, education and skills are all present."
            if not missing_sections
            else f"Add a clear {', '.join(missing_sections)} section.",
        )
    )

    quantified = sum(1 for s in sentences if _NUMBER.search(s))
    out.append(
        HealthCheck(
            id="numbers",
            label="Measurable impact",
            status="pass" if quantified >= 3 else ("warn" if quantified else "fail"),
            detail=f"{quantified} lines include numbers."
            + ("" if quantified >= 3 else " Add results like users served, % faster or bugs fixed."),
        )
    )

    verbs = sum(1 for s in sentences if s.split()[0].lower().strip(",.:") in ACTION_VERBS)
    verbs += sum(1 for w in re.findall(r"[a-z]+", low) if w in ACTION_VERBS) // 3
    out.append(
        HealthCheck(
            id="action_verbs",
            label="Action verbs",
            status="pass" if verbs >= 5 else "warn",
            detail="Bullets lead with strong verbs."
            if verbs >= 5
            else "Start bullets with verbs like Built, Designed, Reduced, Automated.",
        )
    )

    weak = sum(low.count(p) for p in WEAK_PHRASES)
    out.append(
        HealthCheck(
            id="weak_phrases",
            label="Weak phrasing",
            status="pass" if weak == 0 else "warn",
            detail="No passive filler phrases."
            if weak == 0
            else f"{weak} uses of phrases like “responsible for” or “worked on”. Say what you did instead.",
        )
    )

    urls = " ".join(contact.get("urls", [])).lower()
    has_links = any(k in urls or k in low for k in ("github", "linkedin", "portfolio", "gitlab", "behance"))
    out.append(
        HealthCheck(
            id="links",
            label="Profile links",
            status="pass" if has_links else "warn",
            detail="GitHub/LinkedIn link found."
            if has_links
            else "Add your GitHub or LinkedIn so reviewers can see your work.",
        )
    )
    return out

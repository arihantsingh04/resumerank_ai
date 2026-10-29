"""One resume-vs-JD check, start to finish (DESIGN §3). Stateless: nothing is stored."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

import numpy as np

from app.core.errors import ValidationFailed
from app.data.templates import BY_ID
from app.schemas.check import AIReport, Breakdown, JobInfo, Meta, Report, SkillResult
from app.services.health import run_checks
from app.services.ingestion.chunk import chunk_text
from app.services.ingestion.extract import extract_text
from app.services.ingestion.files import detect_file_type
from app.services.ingestion.redact import extract_contact, redact, scrub_name
from app.services.llm.client import LLMError, LLMQuotaExceeded
from app.services.llm.schemas import JobRequirements
from app.services.requirements import RequirementsService
from app.services.scoring import scorer
from app.services.scoring.scorer import Weights
from app.services.scoring.skills import mentions
from app.services.vectorstore.memory_index import MemoryIndex

if TYPE_CHECKING:
    from app.container import Container

log = logging.getLogger(__name__)
WEIGHTS = Weights()  # 0.40 semantic · 0.45 skills · 0.15 experience
MIN_JD_CHARS = 50
MAX_JD_CHARS = 20_000


@dataclass(frozen=True)
class JobSpec:
    title: str
    description: str
    requirements: JobRequirements
    source: Literal["template", "file", "text"]
    requirements_source: Literal["template", "ai", "catalog"]
    template_id: str | None = None


def verdict(score: float) -> Literal["strong", "good", "fair", "low"]:
    if score >= 75:
        return "strong"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "low"


_NAME_LINE = re.compile(r"^[A-Za-z][A-Za-z.'\- ]{1,60}$")


def guess_name(text: str) -> str | None:
    """The first short alphabetic line of a resume is almost always the candidate's name."""
    for line in text.split("\n"):
        line = line.strip()
        if line:
            return line if _NAME_LINE.match(line) and len(line.split()) <= 4 else None
    return None


def _title_from(text: str, fallback: str) -> str:
    first = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    return first[:80] if 2 < len(first) <= 80 else fallback


def _skill_tip(skill: str, required: bool) -> str:
    lead = "This is a must-have for the role." if required else "A bonus that helps you stand out."
    return (
        f"{lead} If you've used {skill}, name it in a project or experience bullet "
        f"with what you built and the "
        f"result. If not, a small weekend project using {skill} is a fast way to close this gap."
    )


class Checker:
    def __init__(self, container: Container) -> None:
        self.c = container
        self.requirements = RequirementsService(container.llm, container.ai_budget)

    # ── job input ─────────────────────────────────────────────────

    def job_from_template(self, template_id: str) -> JobSpec:
        t = BY_ID.get(template_id)
        if t is None:
            from app.core.errors import NotFound

            raise NotFound("That role template doesn't exist.")
        reqs = JobRequirements(
            required_skills=t["required_skills"],
            nice_to_have_skills=t["nice_to_have_skills"],
            min_years_experience=t["min_years"],
        )
        return JobSpec(t["title"], t["description"], reqs, "template", "template", template_id)

    def job_from_text(
        self, text: str, title: str | None, ip: str, source: Literal["file", "text"]
    ) -> JobSpec:
        text = text.strip()
        if len(text) < MIN_JD_CHARS:
            raise ValidationFailed(
                "The job description is too short. Paste the full posting (50+ characters)."
            )
        text = text[:MAX_JD_CHARS]
        reqs, req_source = self.requirements.for_text(text, ip)
        return JobSpec(
            (title or "").strip()[:80] or _title_from(text, "Custom job"), text, reqs, source, req_source
        )

    def job_from_file(self, data: bytes, filename: str, title: str | None, ip: str) -> JobSpec:
        self._check_size(data)
        kind = detect_file_type(data, filename)
        return self.job_from_text(extract_text(data, kind), title, ip, "file")

    def _check_size(self, data: bytes) -> None:
        if len(data) > self.c.settings.max_upload_mb * 1024 * 1024:
            raise ValidationFailed(f"File is too large (max {self.c.settings.max_upload_mb} MB).")

    # ── the check ─────────────────────────────────────────────────

    def read_resume(self, data: bytes, filename: str) -> str:
        self._check_size(data)
        return extract_text(data, detect_file_type(data, filename))

    def analyze(self, resume_text: str, job: JobSpec, ip: str, use_ai: bool = True) -> Report:
        t0 = time.perf_counter()
        s = self.c.settings
        contact = extract_contact(resume_text)
        clean = scrub_name(redact(resume_text), guess_name(resume_text))  # what AI and embeddings see (D-09)

        chunks = chunk_text(clean) or [clean]
        index = MemoryIndex(self.c.encoder.encode(chunks))
        jd_vecs = self.c.encoder.encode(chunk_text(f"{job.title}\n{job.description}") or [job.title])
        jd_vec = jd_vecs.mean(axis=0)
        jd_vec = jd_vec / (np.linalg.norm(jd_vec) or 1)
        semantic = scorer.calibrate(
            float(np.dot(jd_vec, index.mean())), s.semantic_sim_low, s.semantic_sim_high
        )

        reqs = job.requirements
        wanted = [(r, True) for r in reqs.required_skills] + [(r, False) for r in reqs.nice_to_have_skills]
        hits = index.search(self.c.encoder.encode([r for r, _ in wanted]), k=1) if wanted else []
        results: list[SkillResult] = []
        matches: list[scorer.SkillMatch] = []
        for (skill, required), row in zip(wanted, hits, strict=True):
            best_pos, sim = row[0] if row else (None, None)
            literal = mentions(clean, skill)
            res = SkillResult(
                requirement=skill, required=required, similarity=round(sim, 3) if sim is not None else None
            )
            if literal:
                # Quote the resume line itself: chunks flatten line breaks, which glues a job-title
                # line onto the bullet below it.
                holder = next((ln for ln in clean.splitlines() if mentions(ln, skill)), clean)
                res.source, res.evidence = "keyword", scorer.excerpt(holder, skill)
            elif sim is not None and sim >= s.skill_match_threshold and best_pos is not None:
                res.source, res.evidence = "semantic", scorer.excerpt(chunks[best_pos], skill)
            else:
                res.tip = _skill_tip(skill, required)
            results.append(res)
            matches.append(
                scorer.SkillMatch(requirement=skill, required=required, matched=res.source is not None)
            )

        years = scorer.estimate_years(resume_text)
        skills_score = scorer.skill_coverage(matches)
        experience = scorer.experience_score(years, reqs.min_years_experience)
        stage1 = scorer.stage1(semantic, skills_score, experience, WEIGHTS)

        matched = [r for r in results if r.source]
        missing = sorted((r for r in results if not r.source), key=lambda r: not r.required)
        health = run_checks(resume_text, contact)
        tips = self._tips(missing, health)

        ai, ai_score = (
            self._coach(job, clean, matched, missing, health, ip)
            if use_ai
            else (AIReport(status="disabled"), None)
        )
        final = scorer.blend(stage1, ai_score, s.llm_blend)

        ms = int((time.perf_counter() - t0) * 1000)
        log.info(
            "check done: words=%d reqs=%d ai=%s ms=%d", len(resume_text.split()), len(wanted), ai.status, ms
        )
        return Report(
            score=round(final, 1),
            verdict=verdict(final),
            breakdown=Breakdown(
                semantic=round(semantic, 1),
                skills=round(skills_score, 1),
                experience=round(experience, 1),
                ai=ai_score,
            ),
            job=JobInfo(title=job.title, source=job.source, template_id=job.template_id),
            matched=matched,
            missing=missing,
            years_experience=years,
            min_years=reqs.min_years_experience,
            health=health,
            tips=tips,
            ai=ai,
            meta=Meta(
                resume_words=len(resume_text.split()), ms=ms, requirements_source=job.requirements_source
            ),
        )

    @staticmethod
    def _tips(missing: list[SkillResult], health) -> list[str]:
        tips: list[str] = []
        req_missing = [m.requirement for m in missing if m.required]
        if req_missing:
            tips.append(
                f"Mention {', '.join(req_missing[:3])} if you've used them. They're required for this role."
            )
        for h in health:
            if h.status != "pass" and h.id in {
                "numbers",
                "action_verbs",
                "contact",
                "weak_phrases",
                "sections",
            }:
                tips.append(h.detail)
        if not tips:
            tips.append(
                "Tailor your summary line to this job title and lead with your most relevant project."
            )
        return tips[:6]

    def _coach(
        self, job: JobSpec, clean: str, matched, missing, health, ip: str
    ) -> tuple[AIReport, float | None]:
        llm = self.c.llm
        if llm is None:
            return AIReport(status="disabled"), None
        if not self.c.ai_budget.try_acquire(ip):
            return AIReport(status="limited"), None
        signals = {
            "matched_skills": [m.requirement for m in matched],
            "missing_required": [m.requirement for m in missing if m.required],
            "missing_nice_to_have": [m.requirement for m in missing if not m.required],
            "resume_health_issues": [h.detail for h in health if h.status != "pass"],
        }
        try:
            coaching = llm.coach(job.requirements, job.title, clean, signals)
        except LLMQuotaExceeded:
            self.c.ai_budget.refund(ip)
            return AIReport(status="limited"), None
        except LLMError as e:
            log.warning("coaching failed: %s", type(e).__name__)
            self.c.ai_budget.refund(ip)
            return AIReport(status="error"), None
        return AIReport(status="ok", **coaching.model_dump(exclude={"llm_score"})), float(coaching.llm_score)

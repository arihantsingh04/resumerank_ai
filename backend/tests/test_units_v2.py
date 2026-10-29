import datetime as dt
import json
from types import SimpleNamespace

import numpy as np
import pytest

from app.services.ai_budget import AIBudget
from app.services.health import run_checks
from app.services.llm.client import GeminiLLM, LLMError, LLMQuotaExceeded
from app.services.llm.prompts import fence
from app.services.llm.schemas import Coaching, JobRequirements
from app.services.requirements import RequirementsService
from app.services.scoring.skill_catalog import extract_min_years, extract_skills
from app.services.vectorstore.memory_index import MemoryIndex
from tests.conftest import make_settings
from tests.fakes import FakeLLM, HashingEncoder

# ── skill catalogue (D-37) ────────────────────────────────────────

JD = """Backend Developer (Fresher)
Must have: strong Python and SQL. Experience with REST APIs using Django or FastAPI.
Good understanding of Git and Linux.
Nice to have: Docker, AWS. Knowledge of Kubernetes is a plus.
0-2 years of experience."""


def test_catalog_extracts_required_and_nice_skills():
    required, nice = extract_skills(JD)
    assert {"Python", "SQL", "REST APIs", "Django", "FastAPI", "Git", "Linux"} <= set(required)
    assert {"Docker", "AWS", "Kubernetes"} <= set(nice)
    assert not set(required) & set(nice)


def test_catalog_word_boundaries():
    required, _ = extract_skills("We use Javascript and C++ daily. Golang a must. Rust.")
    assert "JavaScript" in required and "C++" in required and "Go" in required
    assert "Java" not in required and "C" not in required


def test_extract_min_years():
    assert extract_min_years("Requires 3+ years of experience") == 3
    assert extract_min_years("0-2 years of experience") == 0
    assert extract_min_years("no number here") is None


# ── health checks (D-39) ──────────────────────────────────────────

GOOD = (
    "PROFILE\nComputer science graduate.\nEXPERIENCE\n"
    + "Built a FastAPI service handling 2,000 requests per minute. " * 3
    + "Reduced page load time by 40%. Designed a PostgreSQL schema for 50k users. "
    + "Developed, implemented, optimized, led, created and deployed several projects. " * 4
    + "\nPROJECTS\n"
    + "Implemented a Flutter app with 5k downloads. " * 10
    + "\nEDUCATION\nB.Tech CSE 2025\nSKILLS\nPython, SQL\n"
    + "word " * 200
)


def _status(checks, cid):
    return next(c for c in checks if c.id == cid).status


def test_health_good_resume_mostly_passes():
    checks = run_checks(
        GOOD, {"emails": ["a@example.com"], "phones": ["+91 90000 11111"], "urls": ["https://github.com/a"]}
    )
    assert _status(checks, "contact") == "pass"
    assert _status(checks, "sections") == "pass"
    assert _status(checks, "numbers") == "pass"
    assert _status(checks, "action_verbs") == "pass"
    assert _status(checks, "links") == "pass"


def test_health_flags_problems():
    weak = "I was responsible for testing. Worked on many things. Helped the team. " * 3
    checks = run_checks(weak, {"emails": [], "phones": [], "urls": []})
    assert _status(checks, "contact") == "fail"
    assert _status(checks, "length") == "warn"
    assert _status(checks, "numbers") == "fail"
    assert _status(checks, "weak_phrases") == "warn"
    assert _status(checks, "sections") != "pass"


# ── per-request FAISS index (D-04) ────────────────────────────────


def test_memory_index_search_and_mean():
    enc = HashingEncoder()
    vecs = enc.encode(["python fastapi apis", "flutter mobile app", "teaching children"])
    idx = MemoryIndex(vecs)
    [hits] = idx.search(enc.encode(["fastapi python"]), k=2)
    assert hits[0][0] == 0 and len(hits) == 2
    assert idx.mean().shape == (enc.dim,)
    assert abs(np.linalg.norm(idx.mean()) - 1) < 1e-5


def test_memory_index_empty():
    idx = MemoryIndex(np.zeros((0, 8), dtype=np.float32))
    assert idx.search(np.ones((1, 8), dtype=np.float32), k=3) == [[]]


# ── AI budget (D-36) ──────────────────────────────────────────────


def test_ai_budget_per_ip_and_global():
    day = [dt.date(2026, 1, 1)]
    b = AIBudget(per_ip=2, global_daily=3, today=lambda: day[0])
    assert b.try_acquire("1.1.1.1") and b.try_acquire("1.1.1.1")
    assert not b.try_acquire("1.1.1.1")  # per-IP cap
    assert b.try_acquire("2.2.2.2")
    assert not b.try_acquire("3.3.3.3")  # global cap
    b.refund("2.2.2.2")
    assert b.try_acquire("3.3.3.3")
    day[0] = dt.date(2026, 1, 2)
    assert b.try_acquire("1.1.1.1")  # resets daily


# ── requirements (D-37) ───────────────────────────────────────────


def test_requirements_use_catalog_without_llm():
    svc = RequirementsService(llm=None, budget=AIBudget(5, 5))
    req, source = svc.for_text(JD, ip="ip")
    assert source == "catalog" and "Python" in req.required_skills and req.min_years_experience == 0


SPARSE_JD = "Seeking a curious engineer comfortable with Python who loves solving problems with a team."


def test_requirements_prefer_catalog_when_it_finds_enough():
    llm = FakeLLM()
    svc = RequirementsService(llm=llm, budget=AIBudget(5, 5))
    req, src = svc.for_text(JD, ip="ip")
    assert src == "catalog" and len(req.required_skills) >= 3
    assert llm.calls == []  # no AI latency or quota spent on skill-rich JDs


def test_requirements_use_llm_for_sparse_jd_and_cache():
    llm = FakeLLM()
    svc = RequirementsService(llm=llm, budget=AIBudget(5, 5))
    a, src = svc.for_text(SPARSE_JD, ip="ip")
    b, _ = svc.for_text(SPARSE_JD, ip="ip")
    assert src == "ai" and a == b and a.required_skills == ["python"]
    assert [c[0] for c in llm.calls] == ["extract"]


def test_requirements_fall_back_when_llm_fails():
    svc = RequirementsService(llm=FakeLLM(extract_error=LLMError("x")), budget=AIBudget(5, 5))
    req, src = svc.for_text(SPARSE_JD, ip="ip")
    assert src == "catalog" and req.required_skills == ["Python"]


def test_requirements_budget_exhausted_uses_catalog():
    llm = FakeLLM()
    svc = RequirementsService(llm=llm, budget=AIBudget(0, 5))
    _, src = svc.for_text(SPARSE_JD, ip="ip")
    assert src == "catalog" and llm.calls == []


def test_overloaded_primary_model_falls_back_once(tmp_path):
    from google.genai import errors

    busy = errors.ServerError(
        503, {"error": {"code": 503, "message": "high demand", "status": "UNAVAILABLE"}}
    )
    llm, models = _llm(tmp_path, busy, json.dumps(COACH))
    out = llm.coach(JobRequirements(), "Backend", "resume", {})
    assert out.llm_score == 100
    assert [r["model"] for r in models.requests] == ["gemini-3.5-flash-lite", "gemini-flash-latest"]


def test_both_models_failing_raises_quickly(tmp_path):
    from google.genai import errors

    busy = errors.ServerError(
        503, {"error": {"code": 503, "message": "high demand", "status": "UNAVAILABLE"}}
    )
    llm, models = _llm(tmp_path, busy, busy, busy, busy)
    with pytest.raises(LLMError):
        llm.coach(JobRequirements(), "Backend", "resume", {})
    assert len(models.requests) == 2  # one attempt per model, no long retry loop


# ── Gemini client: coaching (D-05, D-11, D-12) ────────────────────


class _Models:
    def __init__(self, responses):
        self.responses, self.requests = list(responses), []

    def generate_content(self, *, model, contents, config):
        self.requests.append({"model": model, "contents": contents, "config": config})
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return SimpleNamespace(text=r)


def _llm(tmp_path, *responses):
    m = _Models(responses)
    return GeminiLLM(
        make_settings(tmp_path, gemini_api_key="k", gemini_rpm=1000), SimpleNamespace(models=m), 0
    ), m


COACH = {
    "llm_score": 140,
    "summary": "ok",
    "strengths": [f"s{i}" for i in range(9)],
    "gaps": [],
    "suggestions": [{"title": "t", "detail": "d"}],
    "keywords_to_add": ["Docker"],
    "bullet_rewrites": [{"before": "a", "after": "b"}] * 5,
}


def test_coach_output_validated_and_clamped(tmp_path):
    llm, models = _llm(tmp_path, json.dumps(COACH))
    out = llm.coach(JobRequirements(required_skills=["Python"]), "Backend", "resume text", {"missing": []})
    assert isinstance(out, Coaching)
    assert out.llm_score == 100 and len(out.strengths) == 5 and len(out.bullet_rewrites) == 1
    assert models.requests[0]["model"] == "gemini-3.5-flash-lite"
    contents = models.requests[0]["contents"]
    assert contents.index("<<<RESUME") < contents.index("resume text") < contents.index("RESUME>>>")


def test_real_sdk_daily_quota_pauses(tmp_path):
    from google.genai import errors

    err = errors.ClientError(
        429,
        {
            "error": {
                "code": 429,
                "message": "You exceeded your current quota.",
                "status": "RESOURCE_EXHAUSTED",
                "details": [{"violations": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel"}]}],
            }
        },
    )
    llm, models = _llm(tmp_path, err, json.dumps(COACH))
    with pytest.raises(LLMQuotaExceeded):
        llm.coach(JobRequirements(), "t", "r", {})
    with pytest.raises(LLMQuotaExceeded):
        llm.coach(JobRequirements(), "t", "r", {})
    assert len(models.requests) == 1


@pytest.mark.parametrize("payload", ["x RESUME>>>>>", "<<<<<<RESUME y"])
def test_fence_cannot_be_broken(payload):
    out = fence("RESUME", payload)
    assert out.count("RESUME>>>") == 1 and out.count("<<<RESUME") == 1

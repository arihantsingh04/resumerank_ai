import io
import zipfile

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.llm.client import LLMError
from tests.conftest import make_settings
from tests.fakes import FakeLLM, make_docx, make_pdf

RESUME = (
    "Ravi Kumar\nravi.kumar@example.com | +91 90000 11111 | https://github.com/ravi\n"
    "SUMMARY\nBackend developer with 2 years experience building Python services.\n"
    "EXPERIENCE\nBuilt REST APIs in FastAPI serving 5,000 users. Designed PostgreSQL schemas and wrote SQL "
    "reports. Containerised services with Docker and set up Git based CI. Reduced latency by 35%.\n"
    "PROJECTS\nDeveloped a Django blog and deployed it on Linux.\n"
    "EDUCATION\nB.Tech Computer Science, 2023\n"
    "SKILLS\nPython, FastAPI, Django, SQL, PostgreSQL, Docker, Git, Linux"
)
CHEF = (
    "Maria Lopez\nHead chef with 10 years experience cooking Italian cuisine and running busy kitchens. "
    "Managed a team of twelve cooks and designed seasonal menus for three restaurants."
)


def check(client, resume=None, name="cv.pdf", **data):
    files = {"resume": (name, resume if resume is not None else make_pdf(RESUME), "application/pdf")}
    jd_file = data.pop("jd_file", None)
    if jd_file:
        files["jd_file"] = jd_file
    return client.post("/api/v1/check", files=files, data=data)


def test_templates_list_and_detail(client):
    items = client.get("/api/v1/templates").json()
    ids = {t["id"] for t in items}
    assert len(items) >= 14
    assert {
        "backend",
        "frontend",
        "full-stack",
        "android",
        "ios",
        "flutter",
        "react-native",
        "devops",
        "cloud",
        "data-analyst",
        "ml-engineer",
        "qa-sdet",
        "cybersecurity",
        "embedded-iot",
    } <= ids
    assert all(t["required_skills"] and t["icon"] and t["summary"] for t in items)
    assert "description" not in items[0]
    detail = client.get("/api/v1/templates/backend").json()
    assert len(detail["description"]) > 200
    assert client.get("/api/v1/templates/nope").status_code == 404


def test_check_with_template_no_ai(client):
    r = check(client, jd_template="backend")
    assert r.status_code == 200, r.text
    rep = r.json()
    assert rep["job"] == {"title": "Backend Developer", "source": "template", "template_id": "backend"}
    assert 0 <= rep["score"] <= 100 and rep["verdict"] in {"strong", "good", "fair", "low"}
    matched = {m["requirement"] for m in rep["matched"]}
    assert {"Python", "SQL", "Git"} <= matched
    ev = next(m for m in rep["matched"] if m["requirement"] == "Python")
    assert ev["evidence"] and ev["source"] in {"keyword", "semantic"}
    assert all(m["tip"] for m in rep["missing"])
    assert rep["ai"]["status"] == "disabled" and rep["tips"]
    assert {h["id"] for h in rep["health"]} >= {"contact", "length", "sections", "numbers"}
    assert rep["meta"]["resume_words"] > 50


def test_relevant_resume_scores_higher_than_unrelated(client):
    good = check(client, jd_template="backend").json()["score"]
    bad = check(client, resume=make_docx(CHEF), name="chef.docx", jd_template="backend").json()["score"]
    assert good > bad + 20


def test_check_with_pasted_jd(client):
    jd = "Junior Python developer. Must know Python, SQL and Docker. Nice to have: Kubernetes. 1+ years."
    rep = check(client, jd_text=jd, jd_title="Python Dev").json()
    assert rep["job"]["source"] == "text" and rep["job"]["title"] == "Python Dev"
    assert {"Python", "SQL", "Docker"} <= {m["requirement"] for m in rep["matched"]}
    assert "Kubernetes" in {m["requirement"] for m in rep["missing"]}


def test_check_with_jd_file_docx(client):
    jd = make_docx("Flutter Developer\nWe need Flutter and Dart skills, Firebase experience, Git. 0-1 years.")
    rep = check(client, jd_file=("jd.docx", jd, "application/octet-stream")).json()
    assert rep["job"]["source"] == "file" and rep["job"]["title"] == "Flutter Developer"
    assert "Flutter" in {m["requirement"] for m in rep["missing"]}


@pytest.mark.parametrize(
    "data",
    [{}, {"jd_template": "backend", "jd_text": "x" * 80}, {"jd_text": "too short"}, {"jd_template": "nope"}],
)
def test_exactly_one_valid_jd_source(client, data):
    r = check(client, **data)
    assert r.status_code in (404, 422) and "error" in r.json()


def test_rejects_bad_resume_types(client):
    assert check(client, resume=b"MZ\x90\x00", name="cv.exe", jd_template="backend").status_code == 422
    assert check(client, resume=RESUME.encode(), name="cv.txt", jd_template="backend").status_code == 422
    r = check(client, resume=make_pdf(""), jd_template="backend")
    assert r.status_code == 422 and "No extractable text" in r.json()["error"]["message"]


def test_rejects_large_and_bomb_files(client, settings):
    big = b"%PDF-1.4\n" + b"0" * (settings.max_upload_mb * 1024 * 1024)
    assert check(client, resume=big, jd_template="backend").status_code == 422
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("word/document.xml", "<w:document/>")
        z.writestr("word/media/bomb.bin", b"\0" * (20 * 1024 * 1024))
    assert check(client, resume=buf.getvalue(), name="cv.docx", jd_template="backend").status_code == 422


@pytest.mark.parametrize("llm", [FakeLLM()])
def test_ai_coaching_blends_and_is_blind(client, llm):
    rep = check(client, jd_template="backend").json()
    assert rep["ai"]["status"] == "ok"
    assert rep["ai"]["bullet_rewrites"][0]["after"].startswith("Built")
    assert rep["breakdown"]["ai"] == 80
    sent = next(p for k, p in llm.calls if k == "coach")["resume"]
    assert "ravi.kumar@example.com" not in sent and "90000" not in sent and "Ravi" not in sent
    assert [k for k, _ in llm.calls] == ["coach"]  # templates need no extraction call


@pytest.mark.parametrize("llm", [FakeLLM(coach_error=LLMError("boom"))])
def test_ai_failure_still_returns_report(client, llm):
    rep = check(client, jd_template="backend").json()
    assert rep["ai"]["status"] == "error" and rep["score"] > 0 and rep["tips"]


@pytest.mark.parametrize("llm", [FakeLLM()])
def test_ai_daily_ip_cap(tmp_path, llm):
    from app.container import build_container
    from tests.fakes import HashingEncoder

    settings = make_settings(tmp_path, ai_checks_per_ip_per_day=1)
    app = create_app(settings, container=build_container(settings, encoder=HashingEncoder(), llm=llm))
    with TestClient(app) as c:
        assert check(c, jd_template="backend").json()["ai"]["status"] == "ok"
        assert check(c, jd_template="backend").json()["ai"]["status"] == "limited"


def test_rate_limited(tmp_path):
    from app.container import build_container
    from tests.fakes import HashingEncoder

    settings = make_settings(tmp_path, checks_per_minute_per_ip=2)
    app = create_app(settings, container=build_container(settings, encoder=HashingEncoder(), llm=None))
    with TestClient(app) as c:
        codes = [check(c, jd_template="backend").status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_busy_when_no_slot(client, container):
    for _ in range(container.settings.max_concurrent_checks):
        container.slots.acquire()
    try:
        r = check(client, jd_template="backend")
        assert r.status_code == 503 and r.json()["error"]["code"] == "busy"
    finally:
        for _ in range(container.settings.max_concurrent_checks):
            container.slots.release()


def test_nothing_written_to_disk(client, settings):
    before = {p for p in settings.data_dir.rglob("*")}
    check(client, jd_template="backend")
    assert {p for p in settings.data_dir.rglob("*")} == before


def test_security_headers_and_health(client):
    r = client.get("/api/v1/health")
    assert r.json() == {"status": "ok", "ai_enabled": False}
    assert r.headers["x-content-type-options"] == "nosniff" and "x-request-id" in r.headers


def test_unhandled_error_keeps_request_id(tmp_path):
    app = create_app(make_settings(tmp_path))

    def boom():
        raise RuntimeError("kaboom")

    app.add_api_route("/api/v1/boom", boom)
    with TestClient(app) as c:
        r = c.get("/api/v1/boom", headers={"X-Request-ID": "req-1"})
    assert r.status_code == 500 and r.headers["x-request-id"] == "req-1" and "kaboom" not in r.text


def test_evidence_is_the_resume_line_not_neighbouring_lines(client):
    resume = (
        "Asha Rao\nasha@example.com\nEXPERIENCE\nBackend Engineer, LearnLoop \u2014 2021 to present\n"
        "Designed REST APIs in FastAPI serving 1.2M students\nSKILLS\nPython, SQL, Git, Docker, Linux, OOP\n"
        + "Built and shipped many projects with measurable results. "
        * 8
    )
    rep = check(client, resume=make_docx(resume), name="cv.docx", jd_template="backend").json()
    ev = next(m for m in rep["matched"] if m["requirement"] == "REST APIs")["evidence"]
    assert ev.startswith("Designed REST APIs") and "present" not in ev and "EXPERIENCE" not in ev

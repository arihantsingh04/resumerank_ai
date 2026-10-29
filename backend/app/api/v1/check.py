from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.api.deps import ContainerDep, client_ip
from app.core.errors import AppError, ValidationFailed
from app.schemas.check import Report

router = APIRouter(tags=["check"])
SLOT_WAIT_S = 10


class Busy(AppError):
    status_code = 503
    code = "busy"


def _read(f: UploadFile, limit: int) -> bytes:
    # Read one byte past the limit so oversize files are detected without loading them fully.
    return f.file.read(limit + 1)


@router.post("/check", response_model=Report)
def check(
    request: Request,
    container: ContainerDep,
    resume: Annotated[UploadFile, File(description="Your resume (PDF or DOCX)")],
    jd_template: Annotated[str | None, Form(max_length=40)] = None,
    jd_file: Annotated[UploadFile | None, File(description="Job description (PDF or DOCX)")] = None,
    jd_text: Annotated[str | None, Form(max_length=20_000)] = None,
    jd_title: Annotated[str | None, Form(max_length=80)] = None,
):
    """Sync route on purpose: parsing and embedding are CPU work and run in the threadpool (D-19)."""
    ip = client_ip(request)
    container.check_limiter.check(f"check:{ip}")
    sources = [x for x in (jd_template, jd_file, jd_text and jd_text.strip()) if x]
    if len(sources) != 1:
        raise ValidationFailed("Choose exactly one job source: a template, a JD file or pasted text.")

    if not container.slots.acquire(timeout=SLOT_WAIT_S):
        raise Busy("ResumeRank is busy checking other resumes. Try again in a few seconds.")
    try:
        checker = container.checker
        limit = container.settings.max_upload_mb * 1024 * 1024
        resume_text = checker.read_resume(_read(resume, limit), resume.filename or "resume")
        if jd_template:
            job = checker.job_from_template(jd_template)
        elif jd_file is not None:
            job = checker.job_from_file(_read(jd_file, limit), jd_file.filename or "jd", jd_title, ip)
        else:
            job = checker.job_from_text(jd_text or "", jd_title, ip, "text")
        return checker.analyze(resume_text, job, ip)
    finally:
        container.slots.release()

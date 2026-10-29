"""Test doubles and fixture builders. No network, no model downloads."""

from __future__ import annotations

import hashlib
import io
import re

import numpy as np

# ── Document builders ─────────────────────────────────────────────


def make_pdf(text: str) -> bytes:
    """Build a minimal valid single-page PDF whose text pypdf can extract.

    An empty ``text`` yields a page with no text operators (an "image-only" PDF).
    """
    lines = [ln for ln in text.split("\n")]
    ops = []
    if text:
        ops.append("BT /F1 11 Tf 50 750 Td 14 TL")
        for ln in lines:
            safe = ln.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            ops.append(f"({safe}) Tj T*")
        ops.append("ET")
    stream = "\n".join(ops).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return out.getvalue()


def make_docx(text: str) -> bytes:
    from docx import Document

    doc = Document()
    for para in text.split("\n"):
        doc.add_paragraph(para)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ── LLM fake ──────────────────────────────────────────────────────

KNOWN_SKILLS = ["python", "fastapi", "postgresql", "docker", "react", "sql", "excel", "kubernetes", "flutter"]


class FakeLLM:
    """Implements the LLMClient protocol deterministically. Pass exceptions to simulate failures."""

    def __init__(self, coach_error=None, extract_error=None, score=None):
        self.coach_error = coach_error
        self.extract_error = extract_error
        self.score = score
        self.calls: list[tuple[str, object]] = []

    def extract_requirements(self, jd):
        from app.services.llm.schemas import JobRequirements

        self.calls.append(("extract", jd))
        if self.extract_error:
            raise self.extract_error
        low = jd.lower()
        years = re.search(r"(\d+)\+?\s+years", low)
        return JobRequirements(
            required_skills=[s for s in KNOWN_SKILLS if s in low],
            min_years_experience=float(years.group(1)) if years else None,
        )

    def coach(self, req, job_title, resume_text, signals):
        from app.services.llm.schemas import Coaching

        self.calls.append(("coach", {"resume": resume_text, "signals": signals, "title": job_title}))
        if self.coach_error:
            raise self.coach_error
        return Coaching(
            llm_score=self.score if self.score is not None else 80,
            summary="Solid backend foundation.",
            strengths=["Hands-on FastAPI projects"],
            gaps=["No Kubernetes exposure"],
            suggestions=[{"title": "Quantify impact", "detail": "Add numbers to your project bullets."}],
            keywords_to_add=["Kubernetes"],
            bullet_rewrites=[{"before": "Worked on APIs", "after": "Built 12 REST APIs in FastAPI"}],
        )


# ── Encoder fake ──────────────────────────────────────────────────

_WORD = re.compile(r"[a-z0-9+#]+")


class HashingEncoder:
    """Deterministic bag-of-words encoder: texts sharing words get higher cosine similarity."""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def encode(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            for w in _WORD.findall(t.lower()):
                h = int(hashlib.md5(w.encode(), usedforsecurity=False).hexdigest(), 16)
                out[i, h % self.dim] += 1.0
            n = np.linalg.norm(out[i])
            if n > 0:
                out[i] /= n
        return out

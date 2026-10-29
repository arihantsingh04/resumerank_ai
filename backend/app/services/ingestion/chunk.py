"""Section-aware word chunking for embeddings."""

from __future__ import annotations

HEADINGS = {
    "summary",
    "profile",
    "objective",
    "experience",
    "work experience",
    "professional experience",
    "employment",
    "education",
    "skills",
    "technical skills",
    "projects",
    "certifications",
    "achievements",
    "publications",
    "awards",
    "languages",
    "teaching experience",
    "internships",
}


def _is_heading(line: str) -> bool:
    s = line.strip().rstrip(":")
    if not s or len(s) > 40:
        return False
    if s.lower() in HEADINGS:
        return True
    letters = [c for c in s if c.isalpha()]
    return len(letters) >= 4 and all(c.isupper() for c in letters) and len(s.split()) <= 4


def _sections(text: str) -> list[str]:
    sections: list[list[str]] = [[]]
    for line in text.split("\n"):
        if _is_heading(line) and any(ln.strip() for ln in sections[-1]):
            sections.append([])
        sections[-1].append(line)
    return [" ".join(" ".join(s).split()) for s in sections if " ".join(s).strip()]


def chunk_text(text: str, size: int = 120, overlap: int = 30) -> list[str]:
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    chunks: list[str] = []
    for section in _sections(text):
        words = section.split()
        start = 0
        while start < len(words):
            chunks.append(" ".join(words[start : start + size]))
            if start + size >= len(words):
                break
            start += size - overlap
    return chunks

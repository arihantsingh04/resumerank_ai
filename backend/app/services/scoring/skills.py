"""Skill-name normalisation and literal matching."""

from __future__ import annotations

import re

ALIASES = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "k8s": "kubernetes",
    "ml": "machine learning",
    "dl": "deep learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "postgres": "postgresql",
    "psql": "postgresql",
    "mongo": "mongodb",
    "gcp": "google cloud",
    "aws": "amazon web services",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node": "node.js",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "golang": "go",
    "ci/cd": "ci cd",
}

_PUNCT = re.compile(r"[^\w\s+#.]")


def normalize_skill(s: str) -> str:
    s = s.strip().lower().replace("-", " ").replace("_", " ")
    if s in ALIASES:
        return ALIASES[s]
    s = _PUNCT.sub(" ", s)
    s = " ".join(s.split()).strip(".")
    return ALIASES.get(s, s)


def skill_pattern(skill: str) -> re.Pattern[str]:
    """Word-boundary regex for a skill, tolerant of symbols like C++ / C# / Node.js."""
    norm = skill.strip()
    return re.compile(rf"(?<![\w+#]){re.escape(norm)}(?![\w+#])", re.IGNORECASE)


def mentions(text: str, skill: str) -> re.Match[str] | None:
    candidates = {skill.strip(), normalize_skill(skill)}
    candidates |= {k for k, v in ALIASES.items() if v == normalize_skill(skill) and len(k) > 2}
    for c in candidates:
        if c and (m := skill_pattern(c).search(text)):
            return m
    return None

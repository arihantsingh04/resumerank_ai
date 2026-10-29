"""PII minimisation (D-09): pull contact details out, then remove them from text sent to AI."""

from __future__ import annotations

import re

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
URL = re.compile(
    r"(?:https?://|www\.)[^\s|,;]+|\b(?:linkedin\.com|github\.com|gitlab\.com)/[^\s|,;]+",
    re.IGNORECASE,
)
# Phone-like runs of digits/separators; validated by digit count so year ranges don't match.
PHONE = re.compile(r"(?<![\w/])(?:\+|\()?\d[\d\s().-]{6,}\d(?![\w/])")
DOB = re.compile(
    r"\b(?:DOB|D\.O\.B\.?|Date\s+of\s+Birth|Born(?:\s+on)?)\s*[:\-]?\s*"
    r"(?:\d{1,2}[/.\-]\d{1,2}[/.\-]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9},?\s+\d{4}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})",
    re.IGNORECASE,
)


def _is_phone(match: str) -> bool:
    digits = sum(c.isdigit() for c in match)
    return 10 <= digits <= 15


def _strip_trailing(s: str) -> str:
    return s.rstrip(".,;:)")


def extract_contact(text: str) -> dict[str, list[str]]:
    def uniq(items: list[str]) -> list[str]:
        return list(dict.fromkeys(items))

    no_dob = DOB.sub(" ", text)
    emails = uniq(EMAIL.findall(no_dob))
    without_email = EMAIL.sub(" ", no_dob)
    urls = uniq(_strip_trailing(u) for u in URL.findall(without_email))
    without_urls = URL.sub(" ", without_email)
    phones = uniq(p.strip() for p in PHONE.findall(without_urls) if _is_phone(p))
    return {"emails": emails, "phones": phones, "urls": urls}


def redact(text: str) -> str:
    out = DOB.sub("[DATE_OF_BIRTH]", text)
    out = EMAIL.sub("[EMAIL]", out)
    out = URL.sub("[URL]", out)
    out = PHONE.sub(lambda m: "[PHONE]" if _is_phone(m.group(0)) else m.group(0), out)
    return out


def scrub_name(text: str, name: str | None) -> str:
    """Replace the candidate's full name and each name token (>= 3 chars) with [CANDIDATE]."""
    if not name or not name.strip():
        return text
    out = re.sub(rf"\b{re.escape(name.strip())}\b", "[CANDIDATE]", text, flags=re.IGNORECASE)
    for token in {t for t in re.split(r"[\s.,]+", name) if len(t) >= 3}:
        out = re.sub(rf"\b{re.escape(token)}\b", "[CANDIDATE]", out, flags=re.IGNORECASE)
    return re.sub(r"(?:\[CANDIDATE\]\s*){2,}", "[CANDIDATE] ", out).replace("[CANDIDATE] .", "[CANDIDATE].")

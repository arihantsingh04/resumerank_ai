import pytest

from app.core.errors import ValidationFailed
from app.services.ingestion.chunk import chunk_text
from app.services.ingestion.extract import extract_text
from app.services.ingestion.files import detect_file_type, safe_display_name
from app.services.ingestion.redact import extract_contact, redact, scrub_name
from tests.fakes import make_docx, make_pdf

RESUME = (
    "Asha Verma\nSenior Python Developer with 6 years experience building FastAPI services, "
    "PostgreSQL databases and machine learning pipelines for edtech platforms."
)

# ── file type detection ───────────────────────────────────────────


def test_detects_pdf_and_docx():
    assert detect_file_type(make_pdf(RESUME), "cv.pdf") == "pdf"
    assert detect_file_type(make_docx(RESUME), "cv.DOCX") == "docx"


def test_rejects_txt_files():
    with pytest.raises(ValidationFailed):
        detect_file_type(RESUME.encode(), "cv.txt")


def test_rejects_disallowed_extension():
    with pytest.raises(ValidationFailed):
        detect_file_type(b"MZ\x90\x00", "virus.exe")


def test_rejects_exe_renamed_pdf():
    with pytest.raises(ValidationFailed):
        detect_file_type(b"MZ\x90\x00binary", "resume.pdf")


def test_rejects_docx_with_wrong_magic():
    with pytest.raises(ValidationFailed):
        detect_file_type(make_pdf(RESUME), "resume.docx")


def test_rejects_zip_that_is_not_docx():
    import io
    import zipfile

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("hello.txt", "hi")
    with pytest.raises(ValidationFailed):
        detect_file_type(buf.getvalue(), "resume.docx")


def test_safe_display_name_strips_path():
    assert safe_display_name("..\\..\\etc/passwd\x00.pdf") == "passwd.pdf"
    assert safe_display_name("C:\\Users\\me\\My CV.pdf") == "My CV.pdf"
    assert len(safe_display_name("a" * 500 + ".pdf")) <= 120


# ── extraction ────────────────────────────────────────────────────


def test_extracts_pdf_text():
    assert "FastAPI" in extract_text(make_pdf(RESUME), "pdf")


def test_extracts_docx_text():
    assert "PostgreSQL" in extract_text(make_docx(RESUME), "docx")


def test_image_only_pdf_raises_no_text():
    with pytest.raises(ValidationFailed, match="No extractable text"):
        extract_text(make_pdf(""), "pdf")


def test_corrupt_pdf_raises_validation_failed():
    with pytest.raises(ValidationFailed):
        extract_text(b"%PDF-1.4 garbage garbage", "pdf")


# ── redaction ─────────────────────────────────────────────────────

CONTACT = (
    "Asha Verma | asha.verma@example.com | +91 98765 43210 | (555) 123-4567 | "
    "https://linkedin.com/in/asha | DOB: 12/03/1995\nWorked at Acme 2019-2023 and 2023 - 2024."
)


def test_extract_contact():
    c = extract_contact(CONTACT)
    assert c["emails"] == ["asha.verma@example.com"]
    assert len(c["phones"]) == 2
    assert c["urls"] == ["https://linkedin.com/in/asha"]


def test_redact_email_phone_url():
    r = redact(CONTACT)
    assert "asha.verma@example.com" not in r and "[EMAIL]" in r
    assert "98765" not in r and "123-4567" not in r and "[PHONE]" in r
    assert "linkedin.com" not in r and "[URL]" in r
    assert "1995" not in r and "[DATE_OF_BIRTH]" in r


def test_phone_regex_ignores_years_like_2019_2023():
    r = redact("Worked at Acme 2019-2023 and 2023 - 2024. GPA 8.5/10")
    assert "2019-2023" in r and "2023 - 2024" in r
    assert "[PHONE]" not in r


def test_scrub_name_tokens():
    out = scrub_name("Asha Verma led the team. Ms. Verma also mentored. ASHA wrote docs.", "Asha Verma")
    assert "Asha" not in out and "Verma" not in out and "ASHA" not in out
    assert out.count("[CANDIDATE]") >= 3


def test_scrub_name_ignores_short_tokens_and_none():
    assert scrub_name("Li Wu built Lin", "Li Wu") == "[CANDIDATE] built Lin"
    assert scrub_name("unchanged", None) == "unchanged"


# ── chunking ──────────────────────────────────────────────────────


def test_chunk_overlap_and_bounds():
    words = [f"w{i}" for i in range(300)]
    chunks = chunk_text(" ".join(words), size=120, overlap=30)
    assert all(len(c.split()) <= 120 for c in chunks)
    assert chunks[0].split()[-30:] == chunks[1].split()[:30]
    assert chunks[-1].split()[-1] == "w299"


def test_chunk_splits_at_headings():
    text = "SUMMARY\nPython dev.\nEXPERIENCE\nBuilt APIs at Acme.\nEducation\nB.Tech CSE"
    chunks = chunk_text(text)
    assert len(chunks) == 3
    assert chunks[1].startswith("EXPERIENCE")


def test_chunk_empty_text():
    assert chunk_text("   ") == []

"""Upload validation: extension allowlist + magic-byte verification."""

from __future__ import annotations

import io
import re
import unicodedata
import zipfile
from typing import Literal

from app.core.errors import ValidationFailed

FileKind = Literal["pdf", "docx"]
ALLOWED: dict[str, FileKind] = {".pdf": "pdf", ".docx": "docx"}  # D-41


def _ext(filename: str) -> str:
    name = filename.lower().strip()
    dot = name.rfind(".")
    return name[dot:] if dot != -1 else ""


MAX_DOCX_UNCOMPRESSED = 50 * 1024 * 1024
MAX_DOCX_ENTRIES = 2000
MAX_COMPRESSION_RATIO = 100


def _check_zip_bomb(z: zipfile.ZipFile) -> None:
    """Reject archives that would expand to an unreasonable size when python-docx opens them."""
    infos = z.infolist()
    total = sum(i.file_size for i in infos)
    suspicious = any(
        i.file_size > 1024 * 1024 and i.file_size / max(i.compress_size, 1) > MAX_COMPRESSION_RATIO
        for i in infos
    )
    if len(infos) > MAX_DOCX_ENTRIES or total > MAX_DOCX_UNCOMPRESSED or suspicious:
        raise ValidationFailed("This DOCX is malformed or unusually large and was rejected.")


def detect_file_type(data: bytes, filename: str) -> FileKind:
    kind = ALLOWED.get(_ext(filename))
    if kind is None:
        raise ValidationFailed("Unsupported file type. Upload a PDF or DOCX file.")
    if not data:
        raise ValidationFailed("The file is empty.")
    if kind == "pdf" and not data.startswith(b"%PDF-"):
        raise ValidationFailed("This file isn't a valid PDF.")
    if kind == "docx":
        if not data.startswith(b"PK\x03\x04"):
            raise ValidationFailed("This file isn't a valid DOCX.")
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                if "word/document.xml" not in z.namelist():
                    raise ValidationFailed("This file isn't a valid DOCX.")
                _check_zip_bomb(z)
        except zipfile.BadZipFile as e:
            raise ValidationFailed("This file isn't a valid DOCX.") from e
    return kind


_UNSAFE = re.compile(r"[\x00-\x1f\x7f<>:\"|?*]")


def safe_display_name(filename: str, max_len: int = 120) -> str:
    """Basename only, control/reserved characters removed. Used for display, never as a path."""
    name = unicodedata.normalize("NFC", filename).replace("\\", "/").split("/")[-1]
    name = _UNSAFE.sub("", name).strip() or "resume"
    if len(name) > max_len:
        ext = _ext(name)
        name = name[: max_len - len(ext)] + ext
    return name

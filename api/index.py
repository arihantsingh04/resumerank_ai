"""Vercel serverless entry point: serves the FastAPI app at /api/* (D-46).

Vercel's filesystem is read-only except /tmp, and requests arrive through Vercel's proxy, which sets
x-real-ip itself (clients can't forge it), so the per-IP limits use that header here.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

os.environ.setdefault("ENV", "production")
os.environ.setdefault("DATA_DIR", "/tmp/resumerank")  # noqa: S108 (only writable dir on Vercel; per-instance)
os.environ.setdefault("HF_HOME", "/tmp/hf")  # noqa: S108 (model cache; per-instance)
os.environ.setdefault("EMBEDDING_BACKEND", "onnx")
os.environ.setdefault("TRUSTED_IP_HEADER", "x-real-ip")
os.environ.setdefault("MAX_CONCURRENT_CHECKS", "2")
os.environ.setdefault("MAX_UPLOAD_MB", "4")

from app.main import create_app  # noqa: E402

app = create_app()

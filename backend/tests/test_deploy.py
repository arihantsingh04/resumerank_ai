"""Deployment-related behaviour: encoder backend selection (D-46) and trusted client-IP header."""

import builtins

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.container import build_container
from app.main import create_app
from app.services.embeddings.encoder import LazyOnnxEncoder, LazySentenceTransformerEncoder, build_encoder
from tests.conftest import make_settings
from tests.fakes import HashingEncoder, make_pdf

RESUME = "Python developer. Built FastAPI REST APIs with PostgreSQL and Docker. " * 6


def test_explicit_backends(tmp_path):
    assert isinstance(build_encoder(make_settings(tmp_path, embedding_backend="onnx")), LazyOnnxEncoder)
    assert isinstance(
        build_encoder(make_settings(tmp_path, embedding_backend="torch")), LazySentenceTransformerEncoder
    )


def test_auto_falls_back_to_onnx_without_sentence_transformers(tmp_path, monkeypatch):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "sentence_transformers":
            raise ImportError("not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    assert isinstance(build_encoder(make_settings(tmp_path, embedding_backend="auto")), LazyOnnxEncoder)


def _app(tmp_path, **overrides):
    settings = make_settings(tmp_path, checks_per_minute_per_ip=1, **overrides)
    return create_app(settings, container=build_container(settings, encoder=HashingEncoder(), llm=None))


def _check(c, ip):
    return c.post(
        "/api/v1/check",
        files={"resume": ("cv.pdf", make_pdf(RESUME), "application/pdf")},
        data={"jd_template": "backend"},
        headers={"x-real-ip": ip},
    ).status_code


def test_trusted_ip_header_separates_visitors(tmp_path):
    with TestClient(_app(tmp_path, trusted_ip_header="x-real-ip")) as c:
        assert [_check(c, "1.1.1.1"), _check(c, "2.2.2.2"), _check(c, "1.1.1.1")] == [200, 200, 429]


def test_ip_header_ignored_unless_configured(tmp_path):
    # Without the setting, a client-supplied header must not let anyone dodge the limit.
    with TestClient(_app(tmp_path)) as c:
        assert [_check(c, "1.1.1.1"), _check(c, "2.2.2.2")] == [200, 429]


@pytest.mark.slow
def test_onnx_matches_sentence_transformers(tmp_path):
    """Same model through ONNX Runtime must give (near-)identical embeddings to PyTorch."""
    from app.core.config import get_settings

    models_dir = get_settings().models_dir
    texts = ["Built REST APIs in FastAPI", "Taught Grade 4 maths and English", "Kubernetes and Terraform"]
    onnx = LazyOnnxEncoder("sentence-transformers/all-MiniLM-L6-v2", models_dir).encode(texts)
    torch = LazySentenceTransformerEncoder("sentence-transformers/all-MiniLM-L6-v2", models_dir).encode(texts)
    assert onnx.shape == torch.shape == (3, 384)
    assert np.allclose(np.linalg.norm(onnx, axis=1), 1, atol=1e-4)
    assert (onnx * torch).sum(axis=1).min() > 0.999


def test_vercel_requirements_mirror_server_requirements():
    # Vercel can't follow "-r" includes, so the root file is a copy that must stay in sync.
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]

    def pkgs(p: Path) -> list[str]:
        lines = p.read_text(encoding="utf-8").splitlines()
        return [ln.strip() for ln in lines if ln.strip() and not ln.lstrip().startswith("#")]

    assert pkgs(root / "requirements.txt") == pkgs(root / "backend" / "requirements.txt")

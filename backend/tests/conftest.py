from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.container import build_container
from app.core.config import Settings
from app.main import create_app
from tests.fakes import HashingEncoder


def make_settings(tmp_path, **overrides) -> Settings:
    base = dict(
        _env_file=None,
        env="test",
        data_dir=str(tmp_path),
        gemini_api_key="",
        cors_origins="http://localhost:5173",
    )
    base.update(overrides)
    return Settings(**base)


@pytest.fixture
def settings(tmp_path):
    return make_settings(tmp_path)


@pytest.fixture
def llm():
    """Override in a test (parametrize) to inject a fake LLM. None = Gemini disabled."""
    return None


@pytest.fixture
def container(settings, llm):
    return build_container(settings, encoder=HashingEncoder(), llm=llm)


@pytest.fixture
def app(settings, container):
    return create_app(settings, container=container)


@pytest.fixture
def client(app):
    with TestClient(app, base_url="http://testserver") as c:
        yield c

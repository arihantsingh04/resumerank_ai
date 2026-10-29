import pytest
from pydantic import ValidationError

from app.core.config import Settings


def make(**overrides):
    return Settings(_env_file=None, **overrides)


def test_starts_without_any_secret():
    s = make()
    assert s.gemini_enabled is False


def test_cors_origins_parsed_from_csv():
    assert make(cors_origins="http://a.test, http://b.test").cors_origins == [
        "http://a.test",
        "http://b.test",
    ]


def test_gemini_enabled_with_key():
    assert make(gemini_api_key="abc").gemini_enabled is True


def test_abuse_limits_have_safe_defaults():
    s = make()
    assert (s.checks_per_minute_per_ip, s.ai_checks_per_ip_per_day, s.gemini_daily_budget) == (10, 15, 400)
    assert s.max_concurrent_checks == 4 and s.max_upload_mb == 4  # fits Vercel's 4.5 MB body cap


def test_semantic_bounds_must_be_ordered():
    with pytest.raises(ValidationError):
        make(semantic_sim_low=0.7, semantic_sim_high=0.6)


def test_blank_values_in_env_file_fall_back_to_defaults(tmp_path):
    # .env.example ships every key with an empty value; copying it as-is must still start the app.
    example = (__import__("pathlib").Path(__file__).resolve().parents[2] / ".env.example").read_text(
        encoding="utf-8"
    )
    env_file = tmp_path / ".env"
    env_file.write_text(example, encoding="utf-8")
    s = Settings(_env_file=env_file)
    assert s.gemini_rpm == 10 and s.max_upload_mb == 4 and s.gemini_enabled is False
    assert s.cors_origins == ["http://localhost:5173"] and s.embedding_backend == "auto"


def test_relative_data_dir_resolved():
    assert make(data_dir="./data").data_dir.is_absolute()

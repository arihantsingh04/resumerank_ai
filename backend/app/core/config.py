"""Application settings from environment variables / the repo-root `.env` (never committed)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # env_ignore_empty: a blank value (as shipped in .env.example) means "use the default".
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env", env_file_encoding="utf-8", extra="ignore", env_ignore_empty=True
    )

    env: Literal["development", "production", "test"] = "development"
    data_dir: Path = Path("./data")  # only the embedding-model cache lives here (D-35)
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    # Gemini (optional, D-06)
    gemini_api_key: str = ""
    gemini_parse_model: str = "gemini-3.5-flash-lite"
    gemini_rerank_model: str = "gemini-3.5-flash-lite"  # coaching; fast and reliably available
    gemini_fallback_model: str = "gemini-flash-latest"  # used when the primary model is overloaded
    gemini_rpm: int = Field(10, ge=1)
    gemini_timeout_s: int = 20  # per attempt; at most 2 attempts per AI call

    # Abuse protection without logins (D-36)
    checks_per_minute_per_ip: int = Field(10, ge=1)
    ai_checks_per_ip_per_day: int = Field(15, ge=0)
    gemini_daily_budget: int = Field(400, ge=0)
    max_concurrent_checks: int = Field(4, ge=1, le=32)
    max_upload_mb: int = Field(4, ge=1, le=20)  # Vercel caps request bodies at 4.5 MB
    # Header holding the real client IP, set only behind a proxy that overwrites it (e.g. "x-real-ip" on
    # Vercel). Empty = use the socket address, so clients can't spoof their IP to dodge limits.
    trusted_ip_header: str = ""

    # Scoring
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    # auto = PyTorch Sentence-Transformers if installed, else ONNX Runtime (same model, D-46)
    embedding_backend: Literal["auto", "torch", "onnx"] = "auto"
    semantic_sim_low: float = 0.15
    semantic_sim_high: float = 0.65
    skill_match_threshold: float = 0.55
    llm_blend: float = Field(0.5, ge=0, le=1)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> object:
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @model_validator(mode="after")
    def _check(self) -> Settings:
        if not self.data_dir.is_absolute():
            self.data_dir = (ROOT_DIR / self.data_dir).resolve()
        if self.semantic_sim_high <= self.semantic_sim_low:
            raise ValueError("SEMANTIC_SIM_HIGH must be greater than SEMANTIC_SIM_LOW")
        return self

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key.strip())

    @property
    def models_dir(self) -> Path:
        return self.data_dir / "models"


@lru_cache
def get_settings() -> Settings:
    return Settings()

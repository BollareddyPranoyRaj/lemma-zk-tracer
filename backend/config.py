"""
backend/config.py
─────────────────
Centralised settings loaded from environment / .env file.
All downstream modules import from here — never import os.environ directly.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    app_name: str = "Lemma ZK Tracer — Verifiable Due Diligence"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ── API Keys ──────────────────────────────────────────────────────────────
    openai_api_key: str = Field(default="", description="OpenAI API key")
    anthropic_api_key: str = Field(default="", description="Anthropic API key (optional)")

    # ── Lemma / Observability ─────────────────────────────────────────────────
    lemma_api_key: str = Field(default="", description="Lemma API key for telemetry")
    lemma_pod_id: str = Field(default="", description="Lemma Pod ID")
    otlp_endpoint: str = Field(
        default="http://localhost:4318",
        description="OpenTelemetry collector OTLP/HTTP endpoint",
    )

    # ── Storage ───────────────────────────────────────────────────────────────
    chroma_persist_dir: str = "./data/chroma_db"
    upload_dir: str = "./data/uploads"
    max_upload_mb: int = Field(default=50, ge=1, le=500)

    # ── Chunking ──────────────────────────────────────────────────────────────
    chunk_size_tokens: int = Field(default=512, ge=64, le=2048)
    chunk_overlap_tokens: int = Field(default=64, ge=0, le=512)

    # ── LLM ───────────────────────────────────────────────────────────────────
    llm_api_base: str = Field(default="https://api.openai.com/v1", description="Base URL for the LLM API (OpenAI-compatible)")
    llm_model: str = "gpt-4o"
    llm_temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    llm_max_tokens: int = Field(default=2048, ge=256, le=8192)
    llm_timeout_seconds: int = Field(default=120, ge=10, le=600)

    # ── ZK / Cryptographic Layer ──────────────────────────────────────────────
    # HMAC secret for binding metric→source→doc proofs.
    # In prod this comes from an HSM / KMS; for hackathon use a strong secret.
    proof_hmac_secret: str = Field(
        default="CHANGE_ME_IN_PRODUCTION_32_CHARS_MIN",
        description="HMAC-SHA256 secret for ZK-style verification hashes",
    )

    @field_validator("proof_hmac_secret")
    @classmethod
    def hmac_secret_min_length(cls, v: str) -> str:
        if len(v) < 16:
            raise ValueError("proof_hmac_secret must be at least 16 characters")
        return v

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the singleton Settings instance (cached after first call)."""
    return Settings()

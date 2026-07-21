"""Application settings, loaded from the environment (pydantic-settings)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven configuration for the Fleet API."""

    model_config = SettingsConfigDict(env_prefix="FLEET_", extra="ignore")

    database_url: str = "postgresql+asyncpg://fleet:fleet_dev_pw@localhost:5432/fleet"
    # OIDC / Keycloak
    oidc_issuer: str = "http://localhost:8080/realms/fleet"
    oidc_audience: str = "fleet-api"
    oidc_jwks_url: str = "http://localhost:8080/realms/fleet/protocol/openid-connect/certs"
    # Redis (rate limiting)
    redis_url: str = "redis://localhost:6379/0"
    rate_limit_per_minute: int = 120
    # Web shell (Sprint 3) — browser-side calls to /v1/* need CORS.
    web_origin: str = "http://localhost:3000"
    # LiteLLM gateway (Sprint 2)
    litellm_base_url: str = "http://localhost:4000/v1"
    litellm_master_key: str = "sk-fleet-dev-master"
    # RAG ingestion (Sprint 3)
    minio_endpoint: str = "localhost:9000"
    minio_root_user: str = "fleet"
    minio_root_password: str = "fleet_dev_pw"
    minio_secure: bool = False
    minio_bucket: str = "fleet-documents"
    ingest_redis_url: str = "redis://localhost:6379/1"


def get_settings() -> Settings:
    """Return a fresh Settings instance (call at app creation, not import time)."""
    return Settings()

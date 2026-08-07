from __future__ import annotations

import os
import warnings

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General
    app_version: str = "6.0.0"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")

    sentry_dsn: str | None = None

    # CORS — list of allowed origins. In production this must be explicit.
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:3001"]
    )

    # Databases
    database_url: str = Field(
        default="postgresql+asyncpg://omniai:omniai@localhost:5432/omniai"
    )
    database_url_sync: str = Field(
        default="postgresql://omniai:omniai@localhost:5432/omniai"
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Security / JWT - never empty in production
    jwt_secret: str = Field(default="")
    jwt_secret_previous: list[str] = Field(default_factory=list)
    jwt_algorithm: str = Field(default="HS256")
    jwt_key_version: int = Field(default=1)
    access_token_expire_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_expire_days: int = Field(default=7, ge=1, le=90)
    refresh_token_rotation: bool = Field(default=True)
    token_blacklist_enabled: bool = Field(default=True)

    # OAuth
    oauth_google_client_id: str | None = None
    oauth_google_client_secret: str | None = None
    oauth_github_client_id: str | None = None
    oauth_github_client_secret: str | None = None
    oauth_microsoft_client_id: str | None = None
    oauth_microsoft_client_secret: str | None = None
    oauth_apple_client_id: str | None = None
    oauth_apple_client_secret: str | None = None

    # Object storage
    s3_endpoint: str = Field(default="http://localhost:9000")
    s3_access_key: str = Field(default="minioadmin")
    s3_secret_key: str = Field(default="minioadmin")
    s3_bucket: str = Field(default="omniai-files")
    s3_region: str = Field(default="us-east-1")

    # Payments
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None

    # AI Providers
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_gemini_api_key: str | None = None
    deepseek_api_key: str | None = None
    mistral_api_key: str | None = None
    openrouter_api_key: str | None = None
    nvidia_api_key: str | None = None
    nvidia_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1"
    )

    ollama_base_url: str = Field(default="http://localhost:11434")
    vllm_base_url: str | None = None

    default_ai_provider: str = Field(default="openai")

    qdrant_url: str = Field(default="http://localhost:6333")

    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    # Rate limiting / hardening
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_window_seconds: int = Field(default=60, ge=1)
    trusted_proxies: list[str] = Field(default_factory=list)

    max_upload_size_mb: int = Field(default=50, ge=1, le=500)

    mfa_enabled: bool = Field(default=True)
    mfa_issuer_name: str = Field(default="OmniAI")
    account_lockout_threshold: int = Field(default=5, ge=1)
    account_lockout_minutes: int = Field(default=15, ge=1)
    brute_force_rate_limit: int = Field(default=10, ge=1)
    brute_force_window_seconds: int = Field(default=300, ge=10)

    frontend_url: str = Field(default="http://localhost:3000")

    smtp_host: str | None = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_use_tls: bool = Field(default=True)

    agent_workspace_dir: str = Field(default="./data/agent_workspace")

    # Internal: whether we injected a dev fallback secret
    _used_dev_fallback_secret: bool = False

    @model_validator(mode="after")
    def _enforce_secure_secrets(self) -> Settings:
        env = self.environment.lower()
        is_prod = env in ("production", "prod", "staging")

        # Production hardening: debug must be off
        if is_prod and self.debug:
            raise ValueError(
                "DEBUG must be False when environment is production/staging. "
                "Refusing to start with debug mode enabled. Set DEBUG=False."
            )

        # JWT secret validation
        if not self.jwt_secret:
            if is_prod:
                raise ValueError(
                    "JWT_SECRET must be set to a strong, unique value when environment "
                    "is production/staging. Refusing to start with an empty signing secret."
                )
            # Development fallback: deterministic but non-empty, with warning
            dev_fallback = os.getenv(
                "JWT_SECRET_DEV_FALLBACK",
                "dev-only-jwt-secret-please-change-in-production-64-chars-min-secure",
            )
            if len(dev_fallback) < 32:
                dev_fallback = dev_fallback + "-fallback-padding-to-reach-32-chars!!"
            self.jwt_secret = dev_fallback
            self._used_dev_fallback_secret = True
            warnings.warn(
                "JWT_SECRET is empty and environment is development: using insecure fallback secret. "
                "Set JWT_SECRET for any non-local deployment.",
                UserWarning,
                stacklevel=2,
            )

        # Additional length checks (even in dev, warn if too short)
        if self.jwt_secret and len(self.jwt_secret) < 32:
            if is_prod:
                raise ValueError(
                    f"JWT_SECRET must be at least 32 characters (got {len(self.jwt_secret)})."
                    " Generate a strong secret (e.g. `openssl rand -hex 32`)."
                )
            warnings.warn(
                f"JWT_SECRET is short ({len(self.jwt_secret)} chars). Use >=32 chars for better security.",
                UserWarning,
                stacklevel=2,
            )

        # Previous keys validation
        for prev in self.jwt_secret_previous:
            if prev and len(prev) < 32 and is_prod:
                raise ValueError("One of JWT_SECRET_PREVIOUS values is too short (<32 chars).")

        # CORS: In prod should not be wildcard or localhost
        if is_prod:
            forbidden = {"*", "http://localhost:3000", "http://localhost:3001"}
            if any(o in forbidden or "localhost" in o for o in self.cors_origins):
                warnings.warn(
                    "cors_origins contains localhost or wildcard while in production. "
                    "Configure production origins explicitly via CORS_ORIGINS env.",
                    UserWarning,
                    stacklevel=2,
                )

        # Ensure workspace dir is not empty / root
        if not self.agent_workspace_dir or self.agent_workspace_dir in {"/", ".", "./"}:
            self.agent_workspace_dir = "./data/agent_workspace"

        return self

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in ("production", "prod", "staging")

    @property
    def is_debug(self) -> bool:
        return self.debug and not self.is_production


settings = Settings()


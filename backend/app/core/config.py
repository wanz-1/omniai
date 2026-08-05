from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import List, Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_version: str = "6.0.0"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    sentry_dsn: Optional[str] = None

    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:3001"]

    database_url: str = "postgresql+asyncpg://omniai:omniai@localhost:5432/omniai"
    database_url_sync: str = "postgresql://omniai:omniai@localhost:5432/omniai"
    redis_url: str = "redis://localhost:6379/0"

    jwt_secret: str = ""
    jwt_secret_previous: List[str] = []
    jwt_algorithm: str = "HS256"
    jwt_key_version: int = 1
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    refresh_token_rotation: bool = True
    token_blacklist_enabled: bool = True

    oauth_google_client_id: Optional[str] = None
    oauth_google_client_secret: Optional[str] = None
    oauth_github_client_id: Optional[str] = None
    oauth_github_client_secret: Optional[str] = None
    oauth_microsoft_client_id: Optional[str] = None
    oauth_microsoft_client_secret: Optional[str] = None
    oauth_apple_client_id: Optional[str] = None
    oauth_apple_client_secret: Optional[str] = None

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "omniai-files"
    s3_region: str = "us-east-1"

    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None

    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_gemini_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    mistral_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

    ollama_base_url: str = "http://localhost:11434"
    vllm_base_url: Optional[str] = None

    default_ai_provider: str = "openai"

    qdrant_url: str = "http://localhost:6333"

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    trusted_proxies: List[str] = []

    max_upload_size_mb: int = 50

    mfa_enabled: bool = True
    mfa_issuer_name: str = "OmniAI"
    account_lockout_threshold: int = 5
    account_lockout_minutes: int = 15
    brute_force_rate_limit: int = 10
    brute_force_window_seconds: int = 300

    frontend_url: str = "http://localhost:3000"

    @model_validator(mode="after")
    def _enforce_secure_secrets(self):
        env = self.environment.lower()
        if env in ("production", "prod", "staging"):
            if self.debug:
                raise ValueError(
                    "DEBUG must be False when environment is production/staging. "
                    "Refusing to start with debug mode enabled. Set DEBUG=False in your environment configuration."
                )
            if not self.jwt_secret:
                raise ValueError(
                    "JWT_SECRET must be set to a strong, unique value when environment is production/staging. "
                    "Refusing to start with an empty signing secret."
                )
        return self


settings = Settings()

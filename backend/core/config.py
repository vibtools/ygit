from functools import lru_cache
from typing import Literal
from pydantic import AnyHttpUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "YGIT"
    app_env: Literal["development", "staging", "production", "test"] = "development"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    debug: bool = False
    database_url: str = "postgresql+asyncpg://ygit:ygit_password@localhost:5432/ygit"
    redis_url: str = "redis://localhost:6379/0"
    session_secret: SecretStr = Field(default=SecretStr("change-me-in-production"))
    token_encryption_key: SecretStr = Field(default=SecretStr("change-me-in-production"))
    token_encryption_key_version: str = "v1"
    app_base_url: AnyHttpUrl = "http://localhost:8000"
    post_login_redirect_path: str = "/dashboard"
    keycloak_issuer: AnyHttpUrl = "https://auth.vib.tools/realms/vib"
    keycloak_realm: str = "vib"
    keycloak_client_id: str = "ygit"
    keycloak_client_secret: SecretStr = Field(default=SecretStr("change-me-in-production"))
    keycloak_redirect_uri: str = "http://localhost:8000/api/v1/auth/callback"
    keycloak_post_logout_redirect_uri: str = "http://localhost:8000/"
    oidc_scope: str = "openid profile email"
    oidc_allowed_algorithms: list[str] = Field(default_factory=lambda: ["RS256"])
    oidc_http_timeout_seconds: float = 10.0

    # GitHub App provider integration
    github_app_name: str = "YGIT"
    github_app_slug: str = ""
    github_app_id: str = ""
    github_app_private_key: SecretStr = Field(default=SecretStr(""))
    github_app_webhook_secret: SecretStr = Field(default=SecretStr(""))
    github_app_install_url: AnyHttpUrl = "https://github.com/apps/ygit/installations/new"
    github_api_base_url: AnyHttpUrl = "https://api.github.com"
    session_cookie_name: str = "ygit_session"
    session_cookie_secure: bool = False
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    session_ttl_seconds: int = 60 * 60 * 8
    auth_flow_ttl_seconds: int = 60 * 10
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    log_level: str = "INFO"
    worker_id: str = "local-worker-1"
    queue_name: str = "default"
    worker_poll_interval_seconds: int = 5
    worker_max_attempts: int = 3
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False)

    @field_validator("api_prefix")
    @classmethod
    def validate_api_prefix(cls, value: str) -> str:
        if not value.startswith("/"):
            raise ValueError("API prefix must start with '/'.")
        return value.rstrip("/")

    @field_validator("post_login_redirect_path")
    @classmethod
    def validate_post_login_redirect_path(cls, value: str) -> str:
        if not value.startswith("/") or value.startswith("//"):
            raise ValueError("Post-login redirect path must be a local path.")
        return value

    @field_validator("session_cookie_name")
    @classmethod
    def validate_session_cookie_name(cls, value: str) -> str:
        if not value or any(ch in value for ch in " ;,\r\n\t"):
            raise ValueError("Session cookie name is invalid.")
        return value

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    def validate_production(self) -> None:
        if self.app_env != "production":
            return
        if not str(self.app_base_url).startswith("https://"):
            raise RuntimeError("APP_BASE_URL must use HTTPS in production")
        if not str(self.keycloak_issuer).startswith("https://"):
            raise RuntimeError("KEYCLOAK_ISSUER must use HTTPS in production")
        if not self.session_cookie_secure:
            raise RuntimeError("SESSION_COOKIE_SECURE must be true in production")
        unsafe = {
            "session_secret": self.session_secret.get_secret_value(),
            "token_encryption_key": self.token_encryption_key.get_secret_value(),
            "keycloak_client_secret": self.keycloak_client_secret.get_secret_value(),
        }
        weak = {"change-me-in-production", "secret", "password", ""}
        weak_keys = [key for key, value in unsafe.items() if value in weak]
        if weak_keys:
            raise RuntimeError(f"Unsafe production secret configuration: {', '.join(weak_keys)}")

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_production()
    return settings

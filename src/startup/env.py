# Copyright (c) 2026 Joseph Christopher King
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from startup.config import load_custom_config

# Base directory for resolving relative paths (e.g., locating .env files)
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # --- Basic Configuration ---
    app_name: str = Field(
        default="skeleton-fast-api",
        description="Name of the application",
    )
    app_env: Literal["dev", "staging", "prod", "test"] = Field(
        default="dev",
        description="Current deployment environment",
    )
    debug: bool = Field(
        default=False,
        description="Toggle debug mode and verbose logging",
    )
    host: str = Field(
        default="0.0.0.0",
        description="Bind host address",
    )
    port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Bind port number",
    )

    # --- CORS Configuration ---
    allowed_origins: list[str] = Field(
        default=["*"],
        description="List of allowed CORS origins",
    )

    # --- Authentication Configuration ---
    auth_mode: Literal["none", "basic", "oidc"] = Field(
        default="none",
        description="Active authentication provider ('none', 'basic', or 'oidc')",
    )

    # Basic Auth (Container / Local testing)
    basic_auth_username: str = Field(
        default="admin",
        description="Username for HTTP Basic authentication",
    )
    basic_auth_password: SecretStr = Field(
        default=SecretStr("admin"),
        description="Password for HTTP Basic authentication",
    )

    # OIDC Auth
    oidc_issuer_url: str = Field(
        default="",
        description="OIDC issuer URL (e.g., https://auth.example.com/realms/myrealm)",
    )
    oidc_client_id: str = Field(
        default="",
        description="OIDC client ID / audience expected in tokens",
    )
    oidc_algorithms: list[str] = Field(
        default=["RS256"],
        description="Allowed JWT algorithms for OIDC validation",
    )
    oidc_ssl: bool = Field(
        default=True,
        description="Whether to validate OIDC SSL certificates.",
    )

    # --- Logging Configuration ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Application logging level",
    )
    log_mode: Literal["none"] = Field(
        default="none",
        description="Active logging destination / backend ('none' for console stdout)",
    )

    # --- Cron / Scheduled Jobs Configuration ---
    cron_enabled: bool = Field(
        default=True,
        description="Enable or disable background scheduled jobs",
    )
    cron_heartbeat_interval: int = Field(
        default=60,
        ge=1,
        description="Interval in seconds for the heartbeat cron job",
    )

    # --- Payload / Request Size Limits ---
    max_request_size: int = Field(
        default=10_485_760,
        ge=1,
        description="Global fallback maximum request payload size in bytes (default 10MB)",
    )
    max_json_size: int = Field(
        default=1_048_576,
        ge=1,
        description="Maximum JSON request payload size in bytes (default 1MB)",
    )
    max_upload_size: int = Field(
        default=20_971_520,
        ge=1,
        description="Maximum multipart form and document upload size in bytes (default 20MB)",
    )

    # --- JSON Configuration File ---
    config_path: str | None = Field(
        default=None,
        description="Explicit path to JSON configuration file",
    )
    config_file_loaded: str | None = Field(
        default=None,
        description="Resolved path of JSON configuration file loaded at startup, if found",
    )
    custom_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary nested custom configuration loaded from config.json",
    )

    model_config = SettingsConfigDict(
        env_file=(".env", BASE_DIR / ".env", BASE_DIR.parent / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def model_post_init(self, context: Any) -> None:
        super().model_post_init(context)
        if not self.custom_config:
            loaded_data, loaded_file = load_custom_config(self.config_path)
            self.custom_config = loaded_data
            self.config_file_loaded = loaded_file

    @property
    def is_production(self) -> bool:
        return self.app_env == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

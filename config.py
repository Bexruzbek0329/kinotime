"""
Central configuration — reads from .env via pydantic-settings.
"""
from functools import lru_cache
from typing import List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Telegram ──────────────────────────────────────────
    bot_token: str
    bot_username: str
    admin_ids: str = ""          # "123,456"

    @field_validator("bot_username", mode="before")
    @classmethod
    def clean_bot_username(cls, v: str) -> str:
        if not v:
            return v
        v = str(v).strip()
        for prefix in ("https://t.me/", "http://t.me/", "t.me/"):
            if v.startswith(prefix):
                v = v[len(prefix):]
        return v.lstrip("@").strip()

    # ── PostgreSQL ────────────────────────────────────────
    database_url: str

    # ── Redis ─────────────────────────────────────────────
    redis_url: str

    # ── Admin Panel ───────────────────────────────────────
    admin_secret_key: str
    admin_panel_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"

    # ── CORS ──────────────────────────────────────────────
    cors_origins: str = "http://localhost:3000"

    # ── App ───────────────────────────────────────────────
    debug: bool = False
    log_level: str = "INFO"
    environment: str = "production"

    # ── Rate Limiting ─────────────────────────────────────
    rate_limit_requests: int = 30
    rate_limit_window: int = 60

    # ── Pagination ────────────────────────────────────────
    movies_per_page: int = 5

    # ── Computed ──────────────────────────────────────────
    @property
    def admin_id_list(self) -> List[int]:
        if not self.admin_ids:
            return []
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

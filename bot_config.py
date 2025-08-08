"""Application configuration loaded from environment variables."""

import os
from typing import Set

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


def _require_env(name: str) -> str:
    """Return the value of ``name`` or raise ``ValueError`` if missing."""
    value = os.getenv(name)
    if value is None:
        raise ValueError(f"Environment variable {name} is not set")
    return value


def _parse_admin_ids(value: str | None) -> Set[int]:
    """Parse a comma-separated list of admin identifiers into a set."""
    if not value:
        return set()
    return {int(x) for x in value.split(",") if x.strip()}


class Settings(BaseModel):
    bot_token: str = Field(default_factory=lambda: _require_env("BOT_TOKEN"))
    ton_api_key: str | None = os.getenv("TON_API_KEY")
    tron_api_key: str | None = os.getenv("TRON_API_KEY")
    ton_wallet: str = Field(default_factory=lambda: _require_env("TON_WALLET"))
    usdt_wallet: str = Field(default_factory=lambda: _require_env("USDT_WALLET"))
    database_url: str = Field(default_factory=lambda: _require_env("DATABASE_URL"))
    redis_url: str | None = os.getenv("REDIS_URL")
    admin_password: str = Field(default_factory=lambda: _require_env("ADMIN_PASSWORD"))
    channel_id: str | None = os.getenv("CHANNEL_ID")
    base_webapp_url: str | None = os.getenv("BASE_WEBAPP_URL")
    teleport_api_url: str = os.getenv("TELEPORT_API_URL", "https://teleport.blender")
    admin_ids: Set[int] = Field(default_factory=lambda: _parse_admin_ids(os.getenv("ADMIN_IDS")))


settings = Settings()


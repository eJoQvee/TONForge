from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic import BaseModel, Field
import os

load_dotenv()


class Settings(BaseModel):
    bot_token: str = os.getenv("BOT_TOKEN")
    ton_api_key: str | None = os.getenv("TON_API_KEY")
    tron_api_key: str | None = os.getenv("TRON_API_KEY")
    database_url: str = os.getenv("DATABASE_URL")
    redis_url: str | None = os.getenv("REDIS_URL")
    admin_password: str = os.getenv("ADMIN_PASSWORD")
    channel_id: str | None = os.getenv("CHANNEL_ID")
    base_webapp_url: str = os.getenv("BASE_WEBAPP_URL")
    teleport_api_url: str = os.getenv("TELEPORT_API_URL", "https://teleport.blender")
    admin_ids: set[int] = Field(
        default_factory=lambda: {
            int(x)
            for x in os.getenv("ADMIN_IDS", "").split(",")
            if x.strip()
        }
    )


settings = Settings()

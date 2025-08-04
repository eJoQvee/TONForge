from dotenv import load_dotenv
from pydantic import BaseModel
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


settings = Settings()

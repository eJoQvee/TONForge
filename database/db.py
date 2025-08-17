import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Загружаем .env из корня репо
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

Base = declarative_base()

def to_asyncpg_url(url: str) -> str:
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    # postgres:// -> postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    # добавим +asyncpg если отсутствует
    if url.startswith("postgresql://") and "+asyncpg://" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

def is_remote(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return host not in ("localhost", "127.0.0.1")

RAW_DB_URL = os.getenv("DATABASE_URL", "")
ASYNC_DB_URL = to_asyncpg_url(RAW_DB_URL)

# Определяем SSL: asyncpg не понимает 'sslmode' через SQLAlchemy URL, надо передавать 'ssl' в connect_args
# DB_SSL: "auto" (по умолчанию), "true", "false"
DB_SSL = (os.getenv("DB_SSL", "auto") or "auto").lower()
use_ssl = (DB_SSL == "true") or (DB_SSL == "auto" and is_remote(RAW_DB_URL))

connect_args = {"ssl": True} if use_ssl else {}

engine = create_async_engine(
    ASYNC_DB_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args=connect_args,  # ключевое для SSL
)

SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

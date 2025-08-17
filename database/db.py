# database/db.py
import os
from pathlib import Path
from typing import AsyncGenerator
from contextlib import asynccontextmanager

# --- 1) Автозагрузка .env из корня репозитория ---
try:
    from dotenv import load_dotenv
    REPO_ROOT = Path(__file__).resolve().parents[1]  # .../TONForge
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
    else:
        load_dotenv()  # fallback: если .env лежит в CWD
except Exception:
    # если python-dotenv не установлен или иная мелкая ошибка — просто пропустим
    pass

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# --- 2) ENV и DATABASE_URL с безопасным dev-фолбэком ---
ENV = os.getenv("ENV", "development")  # на Render поставишь ENV=production
DATABASE_URL = os.getenv("DATABASE_URL")

# Dev-фолбэк: если переменная не задана и это НЕ прод — используем SQLite
if not DATABASE_URL and ENV != "production":
    sqlite_path = (Path(__file__).resolve().parents[1] / "tonforge.db").as_posix()
    DATABASE_URL = f"sqlite+aiosqlite:///{sqlite_path}"

# Нормализуем Postgres-URL под asyncpg (на случай postgres:// или postgresql:// без +asyncpg)
def _normalize_database_url(url: str) -> str:
    if not url:
        return url
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url

DATABASE_URL = _normalize_database_url(DATABASE_URL)

# В проде URL обязателен
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Local dev: add to .env or rely on SQLite fallback. "
        "Render: set External connection string in service ENV."
    )

# --- 3) База/движок/сессии ---
class Base(DeclarativeBase):
    pass

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=1800,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# alias для совместимости
async_session = AsyncSessionLocal

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()

async def session_generator() -> AsyncGenerator[AsyncSession, None]:
    async with get_session() as session:
        yield session

import os
import ssl
from pathlib import Path
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager

# --- 1) Автозагрузка .env (не критично в проде) ---
try:
    from dotenv import load_dotenv
    REPO_ROOT = Path(__file__).resolve().parents[1]
    env_path = REPO_ROOT / ".env"
    load_dotenv(dotenv_path=env_path if env_path.exists() else None)
except Exception:
    pass

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# --- 2) ENV и DATABASE_URL с dev-фолбэком на SQLite ---
ENV = os.getenv("ENV", "development")   # на Render: ENV=production
DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

if not DATABASE_URL and ENV != "production":
    sqlite_path = (Path(__file__).resolve().parents[1] / "tonforge.db").as_posix()
    DATABASE_URL = f"sqlite+aiosqlite:///{sqlite_path}"


def _is_sqlite(url: Optional[str]) -> bool:
    return bool(url and url.startswith("sqlite+aiosqlite://"))


def _is_pg(url: Optional[str]) -> bool:
    return bool(url and (
        url.startswith("postgres://")
        or url.startswith("postgresql://")
        or url.startswith("postgresql+asyncpg://")
    ))


def _normalize_database_url(url: Optional[str]) -> Optional[str]:
    """
    Приводим PG-URL к драйверу asyncpg и выбрасываем ?sslmode=... (asyncpg его не понимает).
    """
    if not url:
        return url
    # схема -> asyncpg
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # убрать sslmode из query, если вдруг есть
    if "?" in url:
        base, _, query = url.partition("?")
        parts = [p for p in query.split("&") if not p.lower().startswith("sslmode=")]
        url = base + ("?" + "&".join(parts) if parts else "")
    return url


if _is_pg(DATABASE_URL):
    DATABASE_URL = _normalize_database_url(DATABASE_URL)

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Local dev: add to .env or rely on SQLite fallback. "
        "Render: set External connection string in service ENV."
    )

# --- 3) База/движок/сессии ---
class Base(DeclarativeBase):
    pass


def _build_engine_kwargs(url: str) -> dict:
    # Базово
    kwargs: dict = dict(echo=False, future=True)

    if _is_sqlite(url):
        # Для SQLite не передаём пуловые параметры — иначе будет TypeError
        return kwargs

    # Для PostgreSQL/asyncpg — пулы + SSL
    kwargs.update(
        pool_pre_ping=True,
        pool_recycle=900,
        pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "5")),
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")),
    )
    # Надёжный SSL-контекст (решает ошибки вида CERTIFICATE_VERIFY_FAILED и TLS required)
    ssl_ctx = ssl.create_default_context()
    kwargs["connect_args"] = {
        "ssl": ssl_ctx,
        # отключаем statement cache для pgbouncer-подобных пулеров
        "statement_cache_size": 0,
    }
    return kwargs


engine: AsyncEngine = create_async_engine(DATABASE_URL, **_build_engine_kwargs(DATABASE_URL))

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# alias для совместимости со старым кодом
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

import os
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

# === ENV ===
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. On Render: use the External connection string "
        "from your managed Postgres."
    )

# === Base ===
class Base(DeclarativeBase):
    pass

# === Engine ===
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=1800,
)

# === Session factory ===
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# alias, если где-то уже используется
async_session = AsyncSessionLocal

# === Доступ к сессии ===

@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Использование:
        async with get_session() as session:
            ...
    """
    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()

async def session_generator() -> AsyncGenerator[AsyncSession, None]:
    """
    Для FastAPI: Depends(session_generator)
    """
    async with get_session() as session:
        yield session

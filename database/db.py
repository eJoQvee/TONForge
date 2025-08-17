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

# === 0) ENV ===
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "On Render: use the External Connection string from your Postgres."
    )

# === 1) Base ===
class Base(DeclarativeBase):
    pass

# === 2) Engine ===
# Параметры стабильные для Render: pre_ping + recycle
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    pool_recycle=1800,
)

# === 3) Session factory ===
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# Бэк-совместимое имя, если где-то уже используется
async_session = AsyncSessionLocal

# === 4) Две удобные формы доступа к сессии ===

# 4.1 Контекстный менеджер (удобен в aiogram): 
@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Использование:
        async with get_session() as session:
            await session.execute(...)
    """
    session: AsyncSession = AsyncSessionLocal()
    try:
        yield session
        # commit на твоё усмотрение, чаще делаем явный commit в бизнес-логике
    finally:
        await session.close()

# 4.2 Генератор (подходит для FastAPI Depends, джобов и т.п.)
async def session_generator() -> AsyncGenerator[AsyncSession, None]:
    """
    Использование (FastAPI):
        async def endpoint(session: AsyncSession = Depends(session_generator)):
            ...
    """
    async with get_session() as session:
        yield session

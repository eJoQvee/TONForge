import asyncio
import pytest

pytest.importorskip("sqlalchemy.ext.asyncio")
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from database import models

async def _create_session():
    """Create a temporary in-memory SQLite session for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, async_session()


def test_deposit_with_address():
    async def inner():
        engine, session = await _create_session()
        async with session:
            user = models.User(telegram_id=1)
            session.add(user)
            await session.flush()
            dep = models.Deposit(user_id=user.id, amount=10, currency="USDT", address="ADDR")
            )
            session.add(dep)
            await session.commit()
            assert dep.address == "ADDR"
            assert user.deposits[0] == dep
        await engine.dispose()

    asyncio.run(inner())


def test_withdrawal_with_address():
    async def inner():
        engine, session = await _create_session()
        async with session:
            user = models.User(telegram_id=1)
            session.add(user)
            await session.flush()
            wd = models.Withdrawal(user_id=user.id, amount=5, currency="TON", address="TONADDR")
            session.add(wd)
            await session.commit()
            assert wd.address == "TONADDR"
            assert user.withdrawals[0] == wd
        await engine.dispose()

    asyncio.run(inner())

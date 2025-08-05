import asyncio
import pathlib
import sys

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from database import models  # noqa: E402


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
            dep = models.Deposit(
                user_id=user.id, amount=10, currency="USDT", address="ADDR"
            )
            session.add(dep)
            await session.commit()
            assert dep.address == "ADDR"
        await engine.dispose()

    asyncio.run(inner())


def test_withdrawal_with_address():
    async def inner():
        engine, session = await _create_session()
        async with session:
            user = models.User(telegram_id=1)
            session.add(user)
            await session.flush()
            wd = models.Withdrawal(
                user_id=user.id, amount=5, currency="TON", address="TONADDR"
            )
            session.add(wd)
            await session.commit()
            assert wd.address == "TONADDR"
        await engine.dispose()

    asyncio.run(inner())

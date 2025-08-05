import asyncio
import pathlib
import sys

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from database import models
from services.balance import get_balance


async def _create_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = async_session()
    return engine, session


def test_positive_balance():
    async def inner():
        engine, session = await _create_session()
        async with session:
            user = models.User(telegram_id=1)
            session.add(user)
            await session.flush()
            session.add_all([
                models.Deposit(user_id=user.id, amount=100, currency="USDT"),
                models.Withdrawal(user_id=user.id, amount=50, currency="USDT"),
            ])
            await session.commit()
            balance = await get_balance(session, user.id)
            assert balance["USDT"] == 50
        await engine.dispose()
    asyncio.run(inner())


def test_zero_balance():
    async def inner():
        engine, session = await _create_session()
        async with session:
            user = models.User(telegram_id=1)
            session.add(user)
            await session.flush()
            session.add_all([
                models.Deposit(user_id=user.id, amount=100, currency="USDT"),
                models.Withdrawal(user_id=user.id, amount=100, currency="USDT"),
            ])
            await session.commit()
            balance = await get_balance(session, user.id)
            assert balance["USDT"] == 0
        await engine.dispose()
    asyncio.run(inner())


def test_negative_balance():
    async def inner():
        engine, session = await _create_session()
        async with session:
            user = models.User(telegram_id=1)
            session.add(user)
            await session.flush()
            session.add_all([
                models.Deposit(user_id=user.id, amount=100, currency="USDT"),
                models.Withdrawal(user_id=user.id, amount=150, currency="USDT"),
            ])
            await session.commit()
            balance = await get_balance(session, user.id)
            assert balance["USDT"] == -50
        await engine.dispose()
    asyncio.run(inner())

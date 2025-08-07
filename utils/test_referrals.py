from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from database import models
from utils.referrals import add_referral, distribute_referral_income


async def _create_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    session = async_session()
    return engine, session


def test_add_referral_and_distribution():
    async def inner():
        engine, session = await _create_session()
        async with session:
            u1 = models.User(telegram_id=1)
            u2 = models.User(telegram_id=2)
            u3 = models.User(telegram_id=3)
            session.add_all([u1, u2, u3])
            await session.flush()
            await add_referral(session, u1.id, u2.id)
            await add_referral(session, u2.id, u3.id)
            await distribute_referral_income(session, u3.id, 100, "TON")
            await session.commit()
            ref1 = await session.get(models.User, u1.id)
            ref2 = await session.get(models.User, u2.id)
            assert ref2.balance_ton == 100 * 0.10
            assert ref1.balance_ton == 100 * 0.05
        await engine.dispose()
    asyncio.run(inner())


def test_add_referral_self_reference():
    async def inner():
        engine, session = await _create_session()
        async with session:
            u1 = models.User(telegram_id=1)
            session.add(u1)
            await session.flush()
            await add_referral(session, u1.id, u1.id)
            await session.commit()
            refreshed = await session.get(models.User, u1.id)
            assert refreshed.referrer_id is None
        await engine.dispose()
    asyncio.run(inner())

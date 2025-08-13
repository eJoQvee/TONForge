import asyncio
import pathlib
import sys
import pytest

pytest.importorskip("sqlalchemy.ext.asyncio")
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent))
from database import models  # noqa: E402
from utils.antifraud import check_and_update_ip  # noqa: E402


async def _session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    return engine, async_session()


def test_check_and_update_ip_blocks_duplicates():
    async def inner():
        engine, session = await _session()
        async with session:
            user1 = models.User(telegram_id=1)
            user2 = models.User(telegram_id=2)
            session.add_all([user1, user2])
            await session.commit()
            await check_and_update_ip(session, user1, "1.1.1.1")
            await check_and_update_ip(session, user2, "1.1.1.1")
            await session.refresh(user2)
            assert user2.is_blocked
        await engine.dispose()

    asyncio.run(inner())

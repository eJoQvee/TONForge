import asyncio
from sqlalchemy import select, text
from database.db import get_session
from database import models

LOCK_KEY = 424242  # любое целое

async def acquire_lock(session) -> bool:
    row = await session.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": LOCK_KEY})
    return bool(row.scalar())

async def release_lock(session):
    await session.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": LOCK_KEY})

async def main():
    async with get_session() as session:
        if not await acquire_lock(session):
            return  # уже выполняется где-то ещё
        try:
            cfg = await session.get(models.Settings, 1)  # если у тебя класс называется Settings
            daily = cfg.daily_percent if cfg else 0.023

            # на MVP: считаем доход от суммы активных депозитов в TON и USDT
            users = await session.execute(select(models.User))
            for user in users.scalars().all():
                # если ведёшь отдельные deposits — суммируй активные по пользователю
                # здесь для простоты считаем от текущего баланса
                if user.balance_ton:
                    user.balance_ton += float(user.balance_ton) * daily
                if user.balance_usdt:
                    user.balance_usdt += float(user.balance_usdt) * daily
            await session.commit()
        finally:
            await release_lock(session)

if __name__ == "__main__":
    asyncio.run(main())

from database.db import get_session
from database import models


async def accrue_daily_income():
    """
    Начисляет ежедневный процент всем активным депозитам.
    Вызывать по расписанию (cron/Celery).
    """
    async for session in get_session():
        cfg = await session.get(models.Config, 1)
        percent = cfg.daily_percent if cfg else 0.023
        deposits = await session.execute(
            models.Deposit.__table__.select().where(models.Deposit.is_active)
        )
        for dep in deposits.fetchall():
            user = await session.get(models.User, dep.user_id)
            gain = dep.amount * percent
            if dep.currency == "TON":
                user.balance_ton += gain
            else:
                user.balance_usdt += gain

        await session.commit()

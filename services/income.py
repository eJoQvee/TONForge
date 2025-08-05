from database.db import get_session
from database import models

DAILY_PERCENT = 0.023  # 2.3%


async def accrue_daily_income():
    """
    Начисляет ежедневный процент всем активным депозитам.
    Вызывать по расписанию (cron/Celery).
    """
    async for session in get_session():
        deposits = await session.execute(
            models.Deposit.__table__.select().where(models.Deposit.is_active)
        )
        deposits = deposits.fetchall()

        for dep in deposits:
            user = await session.get(models.User, dep.user_id)
            gain = dep.amount * DAILY_PERCENT
            if dep.currency == "TON":
                user.balance_ton += gain
            else:
                user.balance_usdt += gain

        await session.commit()

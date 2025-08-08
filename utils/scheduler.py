import asyncio
from aiogram import Bot
from sqlalchemy import select

from services.income import accrue_daily_income
from services.income import accrue_daily_income
from services import deposit as deposit_service
from database.db import get_session
from database import models
from utils.i18n import t


async def daily_job():
    while True:
        await accrue_daily_income()
        await asyncio.sleep(24 * 60 * 60)


async def deposit_job(bot: Bot):
    while True:
        async for session in get_session():
            result = await session.execute(
                select(models.Deposit.id, models.Deposit.user_id).where(
                    models.Deposit.is_active.is_(False)
                )
            )
            for dep_id, user_id in result.all():
                confirmed = await deposit_service.check_deposit_status(session, dep_id)
                if confirmed:
                    user = await session.get(models.User, user_id)
                    try:
                        await bot.send_message(
                            user.telegram_id,
                            t(user.language, "deposit_success"),
                        )
                    except Exception:
                        pass
        await asyncio.sleep(60)

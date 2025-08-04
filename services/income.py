import httpx
from bot_config import settings

TRON_API_URL = "https://api.trongrid.io"  # пример

async def check_deposit(address: str, label: str, min_amount: float) -> float:
    """
    Проверка входящей USDT (TRC20) транзакции.
    """
    params = {"address": address, "token": "USDT"}
    headers = {"TRON-PRO-API-KEY": settings.tron_api_key} if settings.tron_api_key else {}
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{TRON_API_URL}/v1/accounts/{address}/transactions/trc20", params=params, headers=headers)
        data = resp.json()
        # TODO: фильтрация по memo/label
    return 0.0
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

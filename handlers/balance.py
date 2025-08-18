# handlers/balance.py
from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database import models

balance_router = Router(name="balance")
router = balance_router  # алиас для совместимости с from .balance import router as balance_router

@balance_router.message(Command("balance"))
async def cmd_balance(message: types.Message):
    """
    Показываем баланс пользователя и примерный дневной доход по активным депозитам.
    """
    async with get_session() as session:  # type: AsyncSession
        # ищем пользователя
        result = await session.execute(
            select(models.User).where(models.User.telegram_id == message.from_user.id)
        )
        user: models.User | None = result.scalar_one_or_none()
        if not user:
            await message.answer("Вы не зарегистрированы. Нажмите /start.")
            return

        # базовая ставка из Config (id=1) или 2.3% по умолчанию
        cfg = await session.get(models.Config, 1)
        daily_percent = cfg.daily_percent if cfg and getattr(cfg, "daily_percent", None) is not None else 0.023

        # активные депозиты пользователя
        q = await session.execute(
            select(models.Deposit.amount, models.Deposit.currency).where(
                models.Deposit.user_id == user.id,
                models.Deposit.is_active.is_(True),
            )
        )
        deposits = q.all()

        # оценка дневного дохода (без учёта валют/конвертации)
        daily_income = sum(amount * daily_percent for amount, _ in deposits) if deposits else 0.0

        text = (
            "<b>Ваш баланс</b>\n"
            f"• TON: <b>{user.balance_ton:.4f}</b>\n"
            f"• USDT: <b>{user.balance_usdt:.2f}</b>\n"
            f"• Примерный доход за сутки: <b>{daily_income:.4f}</b>\n"
            f"• Активных депозитов: <b>{len(deposits)}</b>"
        )
        await message.answer(text)

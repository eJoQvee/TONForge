from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from database.db import get_session
from database import models
from utils.referrals import distribute_referral_income

router = Router()


@router.message(F.text.startswith("/deposit"))
async def cmd_deposit(message: Message):
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Usage: /deposit <amount> <TON|USDT>")
        return
    try:
        amount = float(parts[1])
    except ValueError:
        await message.answer("Invalid amount")
        return
    currency = parts[2].upper()
    if currency not in {"TON", "USDT"}:
        await message.answer("Currency must be TON or USDT")
        return

    async for session in get_session():
        result = await session.execute(
            select(models.User).where(models.User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer("Вы не зарегистрированы. Используйте /start.")
            return
        deposit = models.Deposit(user_id=user.id, amount=amount, currency=currency)
        session.add(deposit)
        if currency == "TON":
            user.balance_ton += amount
        else:
            user.balance_usdt += amount
        await distribute_referral_income(session, user.id, amount, currency)
        await session.commit()

    await message.answer("Депозит успешно добавлен")
    

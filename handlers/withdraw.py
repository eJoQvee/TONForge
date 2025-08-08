from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

from database.db import get_session
from database import models
from utils.i18n import t

MIN_WITHDRAW = 50  # TON or USDT
WAIT_HOURS = 24

router = Router()


@router.message(F.text == "/withdraw")
async def cmd_withdraw(message: Message):
    lang = message.from_user.language_code or "en"
    lang = lang if lang in ("ru", "en") else "en"

    async for session in get_session():
        result = await session.execute(
            select(models.User).where(models.User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer(t(lang, "not_registered"))
            return

        if user.balance_ton < MIN_WITHDRAW and user.balance_usdt < MIN_WITHDRAW:
            await message.answer(t(user.language, "withdraw_min"))
            return

        last_q = await session.execute(
            select(models.Withdrawal)
            .where(models.Withdrawal.user_id == user.id)
            .order_by(models.Withdrawal.requested_at.desc())
            .limit(1)
        )
        last = last_q.scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if last and not last.processed and last.requested_at > now - timedelta(hours=WAIT_HOURS):
            await message.answer(t(user.language, "withdraw_pending"))
            return

        if user.balance_ton >= MIN_WITHDRAW:
            currency = "TON"
            amount = user.balance_ton
            user.balance_ton = 0
        else:
            currency = "USDT"
            amount = user.balance_usdt
            user.balance_usdt = 0

        withdrawal = models.Withdrawal(
            user_id=user.id, amount=amount, currency=currency
        )
        session.add(withdrawal)
        await session.commit()

        await message.answer(t(user.language, "withdraw_requested"))

from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from database.db import get_session
from database import models
from utils.referrals import distribute_referral_income
from utils.i18n import t

MIN_DEPOSIT = 10  # TON or USDT

router = Router()


@router.message(F.text.startswith("/deposit"))
async def cmd_deposit(message: Message):
    lang = message.from_user.language_code or "en"
    lang = lang if lang in ("ru", "en") else "en"

    parts = message.text.split()
    if len(parts) != 3:
        await message.answer(t(lang, "deposit_usage"))
        return
    try:
        amount = float(parts[1])
    except ValueError:
        await message.answer(t(lang, "deposit_invalid_amount"))
        return
    currency = parts[2].upper()
    if currency not in {"TON", "USDT"}:
        await message.answer("Currency must be TON or USDT")
        return

    if amount < MIN_DEPOSIT:
        await message.answer(t(lang, "deposit_min"))
        return

    async for session in get_session():
        result = await session.execute(
            select(models.User).where(models.User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer(t(lang, "not_registered"))
            return
        address = settings.ton_wallet if currency == "TON" else settings.usdt_wallet
        dep = await deposit_service.create_deposit(
            session, user.id, amount, currency, address if currency == "USDT" else None
        )

    await message.answer(
        t(
            user.language,
            "deposit_address",
            amount=amount,
            currency=currency,
            address=address,
            label=dep.id,
        )
    )
    

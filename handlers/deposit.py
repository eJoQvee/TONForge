from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from bot_config import settings
from database.db import get_session
from database import models
from services import deposit as deposit_service
from utils.i18n import t
from utils.notify import notify_channel

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

    async with get_session() as session:
        cfg = await session.get(models.Config, 1)
        min_dep = cfg.min_deposit if cfg else 10
        if amount < min_dep:
            await message.answer(t(lang, "deposit_min", min_deposit=min_dep))
            return
        result = await session.execute(
            select(models.User).where(models.User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer(t(lang, "not_registered"))
            return
        if user.is_blocked:
            await message.answer(t(user.language, "blocked"))
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
    
    await notify_channel(
        message.bot,
        t(
            "en",
            "notify_deposit",
            user_id=message.from_user.id,
            amount=amount,
            currency=currency,
        ),
    )

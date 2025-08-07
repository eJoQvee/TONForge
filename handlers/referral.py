from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from database.db import get_session
from database import models
from utils.referrals import get_referral_stats
from utils.i18n import t

router = Router()


@router.message(F.text == "/referrals")
async def cmd_referrals(message: Message):
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
        stats = await get_referral_stats(session, user.id)
    text = t(
        user.language,
        "referral_stats",
        invited=stats["invited"],
        bonus_ton=stats["bonus_ton"],
        bonus_usdt=stats["bonus_usdt"],
    )
    await message.answer(text)

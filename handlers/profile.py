from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from database.db import get_session
from database import models
from utils.helpers import format_ton
from utils.i18n import t

router = Router()


@router.message(F.text == "/profile")
async def cmd_profile(message: Message):
    async with get_session() as session:
        result = await session.execute(
            select(models.User).where(models.User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            lang = message.from_user.language_code or "en"
            lang = lang if lang in ("ru", "en") else "en"
            await message.answer(t(lang, "not_registered"))
            return
        if user.is_blocked:
            await message.answer(t(user.language, "blocked"))
            return
        text = t(
            user.language,
            "profile",
            ton=format_ton(int(user.balance_ton)),
            usdt=user.balance_usdt,
        )
        await message.answer(text)

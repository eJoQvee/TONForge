from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from database.db import get_session
from database import models
from utils.referrals import get_referral_stats

router = Router()


@router.message(F.text == "/referrals")
async def cmd_referrals(message: Message):
    async for session in get_session():
        result = await session.execute(
            select(models.User).where(models.User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer("Вы не зарегистрированы. Используйте /start.")
            return
        stats = await get_referral_stats(session, user.id)
    text = (
        f"Приглашено: {stats['invited']}\n"
        f"Бонус TON: {stats['bonus_ton']}\n"
        f"Бонус USDT: {stats['bonus_usdt']}"
    )
    await message.answer(text)

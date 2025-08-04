from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select
from database.db import get_session
from database import models

router = Router()


@router.message(F.text == "/profile")
async def cmd_profile(message: Message):
    async for session in get_session():
        result = await session.execute(
            select(models.User).where(models.User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer("Вы не зарегистрированы. Используйте /start.")
            return
        text = (
            f"Баланс TON: {user.balance_ton}\n"
            f"Баланс USDT: {user.balance_usdt}"
        )
        await message.answer(text)

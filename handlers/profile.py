from aiogram import Router, F
from aiogram.types import Message
from database.db import get_session
from database import models

router = Router()


@router.message(F.text == "/profile")
async def cmd_profile(message: Message):
    async for session in get_session():
        user = await session.get(models.User, message.from_user.id)
        if not user:
            await message.answer("Вы не зарегистрированы. Используйте /start.")
            return
        text = (f"Баланс TON: {user.balance_ton}\n"
                f"Баланс USDT: {user.balance_usdt}")
        await message.answer(text)

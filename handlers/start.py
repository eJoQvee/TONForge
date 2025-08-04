from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select
from database.db import get_session
from database import models

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message):
    ref_id = None
    if message.get_args():
        try:
            ref_id = int(message.get_args())
        except ValueError:
            pass

    async for session in get_session():
        result = await session.execute(
            select(models.User).where(models.User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            user = models.User(
                telegram_id=message.from_user.id,
                language=message.from_user.language_code or "ru",
                referrer_id=ref_id,
            )
            session.add(user)
            await session.commit()

    await message.answer("Добро пожаловать в TONForge! Используйте /profile для просмотра профиля.")

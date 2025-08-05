from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject
from sqlalchemy import select
from database.db import get_session
from database import models

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    ref_id = None
    if command.args:
        try:
            ref_id = int(command.args)
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

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart, CommandObject
from sqlalchemy import select

from database.db import get_session
from database import models
from utils.referrals import add_referral
from utils.i18n import t

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
            lang = message.from_user.language_code or "en"
            lang = lang if lang in ("ru", "en") else "en"
            user = models.User(telegram_id=message.from_user.id, language=lang)
            session.add(user)
            await session.commit()
        if ref_id:
            await add_referral(session, ref_id, user.id)

    await message.answer(t(user.language, "welcome"))

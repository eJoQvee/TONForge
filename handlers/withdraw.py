from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select
from database.db import get_session
from database import models
from utils.i18n import t

MIN_WITHDRAW = 50  # TON или USDT

router = Router()


@router.message(F.text == "/withdraw")
async def cmd_withdraw(message: Message):
    lang = message.from_user.language_code or "en"
    lang = lang if lang in ("ru", "en") else "en"

    async for session in get_session():
        result = await session.execute(
            select(models.User).where(models.User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await await message.answer(t(lang, "not_registered"))
            return

        if user.balance_ton < MIN_WITHDRAW and user.balance_usdt < MIN_WITHDRAW:
            await message.answer(t(user.language, "withdraw_min"))
            return

        # здесь должна быть логика заявки на вывод (подтверждение, запись в БД и пр.)
        await message.answer(t(user.language, "withdraw_requested"))

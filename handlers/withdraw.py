from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select
from database.db import get_session
from database import models

MIN_WITHDRAW = 50  # TON или USDT

router = Router()


@router.message(F.text == "/withdraw")
async def cmd_withdraw(message: Message):
    async for session in get_session():
        result = await session.execute(
            select(models.User).where(models.User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        if not user:
            await message.answer("Сначала /start.")
            return

        if user.balance_ton < MIN_WITHDRAW and user.balance_usdt < MIN_WITHDRAW:
            await message.answer("Минимальная сумма для вывода 50 TON или 50 USDT.")
            return

        # здесь должна быть логика заявки на вывод (подтверждение, запись в БД и пр.)
        await message.answer("Заявка на вывод отправлена. Ожидайте обработки в течение 24 часов.")

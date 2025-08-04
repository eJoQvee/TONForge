from aiogram import Router, F
from aiogram.types import Message
from database.db import get_session
from database import models

MIN_WITHDRAW = 50  # TON или USDT

router = Router()


@router.message(F.text == "/withdraw")
async def cmd_withdraw(message: Message):
    async for session in get_session():
        user = await session.get(models.User, message.from_user.id)
        if not user:
            await message.answer("Сначала /start.")
            return

        if user.balance_ton < MIN_WITHDRAW and user.balance_usdt < MIN_WITHDRAW:
            await message.answer("Минимальная сумма для вывода 50 TON или 50 USDT.")
            return

        # здесь должна быть логика заявки на вывод (подтверждение, запись в БД и пр.)
        await message.answer("Заявка на вывод отправлена. Ожидайте обработки в течение 24 часов.")

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "/start - регистрация\n"
        "/profile - профиль и баланс\n"
        "/withdraw - вывести средства\n"
    )
    await message.answer(text)

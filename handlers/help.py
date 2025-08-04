from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message(commands={"help"})
async def cmd_help(message: Message):
    text = (
        "/start - регистрация\n"
        "/profile - профиль и баланс\n"
        "/withdraw - вывести средства\n"
    )
    await message.answer(text)

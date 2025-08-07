from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from utils.i18n import t

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    lang = message.from_user.language_code or "en"
    lang = lang if lang in ("ru", "en") else "en"
    await message.answer(t(lang, "help"))

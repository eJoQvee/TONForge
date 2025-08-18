from aiogram import Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from aiogram.filters import CommandStart, CommandObject
from sqlalchemy import select

from database.db import get_session
from database import models
from utils.referrals import add_referral
from utils.i18n import t
from bot_config import settings

# Экспортируем именно start_router
start_router = Router(name="start")


@start_router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    # читаем ref-id из /start <args>
    ref_id = None
    if command.args:
        try:
            ref_id = int(command.args)
        except ValueError:
            ref_id = None

    # Работа с БД — через контекстный менеджер
    async with get_session() as session:
        result = await session.execute(
            select(models.User).where(models.User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            lang = (message.from_user.language_code or "en").lower()
            lang = lang if lang in ("ru", "en") else "en"
            user = models.User(telegram_id=message.from_user.id, language=lang)
            session.add(user)
            await session.commit()

        # запрещаем самореферал; остальное на стороне add_referral()
        if ref_id and ref_id != user.id:
            await add_referral(session, ref_id, user.id)
            await session.commit()

    # Клавиатура
    keyboard_buttons = [
        [KeyboardButton(text="/profile"), KeyboardButton(text="/referrals")],
        [KeyboardButton(text="/deposit 10 TON"), KeyboardButton(text="/withdraw")],
    ]

    if getattr(settings, "base_webapp_url", None):
        url = f"{settings.base_webapp_url}?user_id={message.from_user.id}"
        keyboard_buttons.append(
            [
                KeyboardButton(
                    text=t(user.language, "open_app"),
                    web_app=WebAppInfo(url=url),
                )
            ]
        )

    reply_kb = ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)
    await message.answer(t(user.language, "welcome"), reply_markup=reply_kb)

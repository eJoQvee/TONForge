from __future__ import annotations

import os
from typing import Optional

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session  # async context manager -> "async with"
from database import models
from utils.i18n import t  # у тебя уже используется в других хендлерах
from utils.antifraud import check_and_update_ip
from bot_config import settings

router = Router()

# --- WebApp URL ---
BASE_WEBAPP = os.getenv("BASE_WEBAPP_URL", "https://tonforge-web.onrender.com").rstrip("/")
WEBAPP_PATH = os.getenv("WEBAPP_PATH", "/app")
WEBAPP_URL = f"{BASE_WEBAPP}{WEBAPP_PATH}"

def _bot_username() -> str:
    return getattr(settings, "bot_username", None) or os.getenv("BOT_USERNAME", "TONForge1_bot")

def _parse_ref_payload(text: str) -> Optional[int]:
    """
    Достаём реферальный payload из /start <payload>.
    Допускаем '123', 'ref_123', 'user_123'. Возвращаем int или None.
    """
    parts = (text or "").split(maxsplit=1)
    if len(parts) < 2:
        return None
    payload = parts[1].strip()
    # допускаем несколько форм
    for p in (payload, payload.replace("ref_", ""), payload.replace("user_", "")):
        if p.isdigit():
            try:
                return int(p)
            except Exception:
                pass
    return None

async def _get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    language: str,
    ip: Optional[str],
    referrer_tg_id: Optional[int],
) -> models.User:
    """
    Создаём пользователя при первом /start.
    Если пришёл валидный реферал — заполняем referrer_id (один раз).
    """
    res = await session.execute(select(models.User).where(models.User.telegram_id == telegram_id))
    user = res.scalar_one_or_none()

    if not user:
        user = models.User(
            telegram_id=telegram_id,
            language=("ru" if language == "ru" else "en"),
            balance_ton=0.0,
            balance_usdt=0.0,
            is_blocked=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    # Обновим язык, если поменялся
    new_lang = "ru" if language == "ru" else "en"
    if getattr(user, "language", "en") != new_lang:
        user.language = new_lang

    # Привяжем реферера (только если ещё не привязан и payload валиден)
    if referrer_tg_id and not getattr(user, "referrer_id", None):
        if referrer_tg_id != telegram_id:
            # найдём реферера по его telegram_id
            q = await session.execute(select(models.User).where(models.User.telegram_id == referrer_tg_id))
            ref_user = q.scalar_one_or_none()
            if ref_user:
                user.referrer_id = ref_user.id

    # Антифрод: сохраним IP (если есть)
    if ip:
        await check_and_update_ip(session, user, ip)

    await session.commit()
    await session.refresh(user)
    return user

def _webapp_button(text: str = "Open TONForge") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=text, web_app=WebAppInfo(url=WEBAPP_URL))]
        ]
    )

@router.message(CommandStart())
async def start(message: Message):
    """
    /start [payload]
    - создаём/обновляем пользователя
    - сохраняем реферала (если payload валиден)
    - даём кнопку WebApp на /app
    """
    lang = (message.from_user.language_code or "en").lower()
    lang = "ru" if lang.startswith("ru") else "en"

    ref_payload = _parse_ref_payload(message.text or "")
    ip = message.chat_shared or None  # в приватных чатах IP не доступен, оставляем None

    async with get_session() as session:
        # Создадим пользователя (или обновим язык/реферала)
        await _get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            language=lang,
            ip=None,  # IP от Telegram мы не узнаем, оставим None
            referrer_tg_id=ref_payload,
        )

    # Текст приветствия (через i18n либо fallback)
    greeting = t(lang, "welcome", bot=_bot_username()) if callable(t) else f"Welcome to @{_bot_username()}!"
    hint = t(lang, "open_webapp_hint") if callable(t) else "Tap the button below to open the app."

    await message.answer(
        f"{greeting}\n\n{hint}",
        reply_markup=_webapp_button("Open TONForge"),
    )

@router.message(Command("app"))
async def open_app(message: Message):
    """
    Запасная команда на случай, если нужно повторно показать кнопку WebApp.
    """
    lang = (message.from_user.language_code or "en").lower()
    lang = "ru" if lang.startswith("ru") else "en"
    text = t(lang, "open_webapp_hint") if callable(t) else "Tap the button to open the app."
    await message.answer(text, reply_markup=_webapp_button("Open TONForge"))

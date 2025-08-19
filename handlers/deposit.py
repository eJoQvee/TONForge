from __future__ import annotations

import os

from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select

from bot_config import settings
from database.db import get_session
from database import models
from services import deposit as deposit_service
from utils.i18n import t
from utils.notify import notify_channel

# Экспортируем именно deposit_router — так его импортируют в handlers/__init__.py
deposit_router = Router()


@deposit_router.message(F.text.startswith("/deposit"))
async def cmd_deposit(message: Message):
    # язык
    lang = (message.from_user.language_code or "en").lower()
    if lang not in ("ru", "en"):
        lang = "en"

    # парсим команду: /deposit <amount> <currency>
    parts = (message.text or "").split()
    if len(parts) != 3:
        await message.answer(t(lang, "deposit_usage"))
        return

    try:
        amount = float(parts[1])
    except ValueError:
        await message.answer(t(lang, "deposit_invalid_amount"))
        return

    currency = parts[2].upper()
    if currency not in {"TON", "USDT"}:
        await message.answer("Currency must be TON or USDT")
        return

    # кошельки из settings/ENV
    ton_wallet = getattr(settings, "ton_wallet", os.getenv("TON_WALLET", ""))
    usdt_wallet = getattr(settings, "usdt_wallet", os.getenv("USDT_WALLET", ""))

    # работаем с БД
    async with get_session() as session:
        res = await session.execute(
            select(models.User).where(models.User.telegram_id == message.from_user.id)
        )
        user = res.scalar_one_or_none()
        if not user:
            await message.answer(t(lang, "not_registered"))
            return
        if user.is_blocked:
            await message.answer(t(user.language, "blocked"))
            return

        # создаём НЕактивный депозит (без поля address — его нет в модели)
        try:
            dep = await deposit_service.create_deposit(session, user.id, amount, currency)
        except ValueError as e:
            await message.answer(str(e))
            return

        # label — используем id депозита
        label = deposit_service.deposit_label(dep, fallback_user_tg_id=message.from_user.id)

    # формируем инструкцию пользователю
    if currency == "TON":
        if not ton_wallet:
            await message.answer("TON wallet is not configured.")
            return
        instr = t(
            lang,
            "deposit_address",
            amount=amount,
            currency=currency,
            address=ton_wallet,
            label=label,
        )
    else:
        if not usdt_wallet:
            await message.answer("USDT (TRC-20) wallet is not configured.")
            return
        instr = t(
            lang,
            "deposit_address",
            amount=amount,
            currency=currency,
            address=usdt_wallet,
            label=label,
        )

    await message.answer(instr)

    # уведомление в канал (работает, если CHANNEL_ID корректный и бот есть в канале/группе)
    await notify_channel(
        message.bot,
        t(
            "en",
            "notify_deposit",
            user_id=message.from_user.id,
            amount=amount,
            currency=currency,
        ),
    )

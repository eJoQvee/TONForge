from __future__ import annotations

import hmac
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from urllib.parse import parse_qsl

from fastapi import Depends, HTTPException, Header, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database import models

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ENV = os.getenv("ENV", "development").lower()

def _parse_init_data(init_data: str) -> Dict[str, str]:
    # Телеграм шлёт URL-encoded строку вида k=v&k2=v2...
    pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=False))
    return pairs

def _build_data_check_string(pairs: Dict[str, str]) -> str:
    parts = []
    for k in sorted(pairs.keys()):
        if k == "hash":
            continue
        parts.append(f"{k}={pairs[k]}")
    return "\n".join(parts)

def _hash_login_widget(data_check_string: str, bot_token: str) -> str:
    # Логин-виджет: key = sha256(bot_token), HMAC(key, data_check_string)
    key = hashlib.sha256(bot_token.encode()).digest()
    return hmac.new(key, data_check_string.encode(), hashlib.sha256).hexdigest()

def _hash_webapp_data(data_check_string: str, bot_token: str) -> str:
    # WebApp: key = HMAC("WebAppData", bot_token), HMAC(key, data_check_string)
    key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    return hmac.new(key, data_check_string.encode(), hashlib.sha256).hexdigest()

def verify_init_data(init_data: str) -> Dict[str, Any]:
    """
    Возвращает dict с ключами: user(=dict), auth_date(int), hash(str), ...
    Бросает 401 при неверной подписи.
    Принимаем обе схемы хеширования (на всякий случай).
    """
    if not init_data:
        raise HTTPException(status_code=401, detail="Missing initData")

    pairs = _parse_init_data(init_data)
    provided_hash = pairs.get("hash", "")
    if not provided_hash:
        raise HTTPException(status_code=401, detail="Missing hash")

    dcs = _build_data_check_string(pairs)
    h1 = _hash_login_widget(dcs, BOT_TOKEN)
    h2 = _hash_webapp_data(dcs, BOT_TOKEN)
    if provided_hash != h1 and provided_hash != h2:
        raise HTTPException(status_code=401, detail="Bad initData signature")

    # проверка срока (не строго обязательно)
    try:
        auth_date = int(pairs.get("auth_date", "0"))
        if auth_date:
            dt = datetime.fromtimestamp(auth_date, tz=timezone.utc)
            # Можно ограничить, например, часом давности
    except Exception:
        pass

    # user — JSON строка
    user_raw = pairs.get("user") or "{}"
    try:
        user_obj = json.loads(user_raw)
    except Exception:
        user_obj = {}

    pairs["user"] = user_obj
    return pairs  # словарь с user/auth_date/и т.д.

async def get_current_user(
    session: AsyncSession = Depends(get_session),
    init_data_header: Optional[str] = Header(default=None, alias="X-Telegram-Init-Data"),
    init_data_query: Optional[str] = Query(default=None, alias="init_data"),
    user_id_debug: Optional[int] = Query(default=None, alias="user_id"),
) -> models.User:
    """
    Зависимость для эндпоинтов:
      - В проде: ждём initData в заголовке/параметре и проверяем подпись.
      - В деве: допускаем ?user_id=... (быстрое тестирование с локалки).
    """
    if ENV != "production" and user_id_debug:
        res = await session.execute(
            select(models.User).where(models.User.telegram_id == user_id_debug)
        )
        user = res.scalar_one_or_none()
        if not user:
            user = models.User(telegram_id=user_id_debug, language="en")
            session.add(user)
            await session.commit()
        return user

    init_data = init_data_header or init_data_query or ""
    data = verify_init_data(init_data)
    tg_user = data.get("user") or {}
    tg_id = tg_user.get("id")
    if not tg_id:
        raise HTTPException(status_code=401, detail="No Telegram user id")

    # найдём/создадим пользователя
    res = await session.execute(
        select(models.User).where(models.User.telegram_id == int(tg_id))
    )
    user = res.scalar_one_or_none()
    if not user:
        lang = (tg_user.get("language_code") or "en").lower()
        if lang not in ("ru", "en"):
            lang = "en"
        user = models.User(telegram_id=int(tg_id), language=lang)
        session.add(user)
        await session.commit()
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")
    return user

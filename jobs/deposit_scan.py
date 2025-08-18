# jobs/deposit_scan.py
import asyncio
import os
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import select, insert, text
from database.db import get_session
from database import models

TON_API_KEY = os.getenv("TON_API_KEY")
TON_WALLET   = os.getenv("TON_WALLET")
TRON_API_KEY = os.getenv("TRON_API_KEY")
USDT_WALLET  = os.getenv("USDT_WALLET")

SCAN_WINDOW_MIN = int(os.getenv("SCAN_WINDOW_MIN", "10"))  # глубина окна просмотра, минут

async def save_tx(session, *, user_id, amount, currency, tx_hash, source, label):
    # идемпотентность — не дублируем
    await session.execute(
        insert(models.Transaction)
        .values(user_id=user_id, amount=amount, currency=currency,
                tx_hash=tx_hash, source=source, label=label, status="confirmed")
        .prefix_with("ON CONFLICT (tx_hash) DO NOTHING")
    )
    # Обновим баланс пользователя
    user = await session.get(models.User, user_id)
    if currency == "TON":
        user.balance_ton = (user.balance_ton or 0) + float(amount)
    else:
        user.balance_usdt = (user.balance_usdt or 0) + float(amount)
    await session.commit()

async def find_user_by_label(session, label: str) -> models.User | None:
    # твои лейблы — это id депозита/пользователя; самый простой вариант — считать label == telegram_id
    # лучше: при generate_label создавать предварительную запись deposit с id=label и user_id
    try:
        user_id = int(label)
    except Exception:
        return None
    result = await session.execute(select(models.User).where(models.User.telegram_id == user_id))
    return result.scalar_one_or_none()

async def scan_ton(session):
    if not (TON_API_KEY and TON_WALLET):
        return
    since = datetime.now(timezone.utc) - timedelta(minutes=SCAN_WINDOW_MIN)
    # пример запроса к TonAPI (упростил; подправим поля, когда увидим формат твоего API ответа)
    url = f"https://tonapi.io/v2/accounts/{TON_WALLET}/transactions?limit=100"
    headers = {"Authorization": f"Bearer {TON_API_KEY}"}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()

    # пробегаем входящие, читаем comment/payload -> label
    for tx in data.get("transactions", []):
        if tx.get("utime") and datetime.fromtimestamp(tx["utime"], tz=timezone.utc) < since:
            continue
        # фильтр на входящие на наш адрес:
        # ... (подправим при интеграции)
        tx_hash = tx.get("hash")
        comment = (tx.get("in_msg", {}) or {}).get("message", "")  # бывает в разных полях
        label = (comment or "").strip()
        if not label:
            continue
        user = await find_user_by_label(session, label)
        if not user:
            continue
        amount = float(tx.get("in_msg", {}).get("value", 0)) / 1e9  # TON в нано-тонах
        if amount <= 0:
            continue
        await save_tx(session, user_id=user.id, amount=amount, currency="TON",
                      tx_hash=tx_hash, source="TON", label=label)
        # TODO: здесь же начисляем реферальный бонус (см. шаг 5.4)

async def scan_tron(session):
    if not (TRON_API_KEY and USDT_WALLET):
        return
    since = datetime.now(timezone.utc) - timedelta(minutes=SCAN_WINDOW_MIN)
    # пример TronGrid — нужно подставить твои эндпоинты/параметры
    url = f"https://api.trongrid.io/v1/accounts/{USDT_WALLET}/transactions/trc20?limit=100&only_to=true"
    headers = {"TRON-PRO-API-KEY": TRON_API_KEY}
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()

    for tx in data.get("data", []):
        # фильтр по USDT контракту и по дате
        # label обычно передают в memo — подставь твою логику получения label
        memo = (tx.get("raw_data", {}) or {}).get("data", "")
        label = memo.strip()
        if not label:
            continue
        user = await find_user_by_label(session, label)
        if not user:
            continue
        if tx.get("token_info", {}).get("symbol") != "USDT":
            continue
        amount = float(tx.get("value", 0)) / 1e6  # USDT имеет 6 знаков
        if amount <= 0:
            continue
        tx_hash = tx.get("transaction_id")
        await save_tx(session, user_id=user.id, amount=amount, currency="USDT",
                      tx_hash=tx_hash, source="TRON", label=label)
        # TODO: здесь же начисляем реферальный бонус (см. шаг 5.4)

async def main():
    async with get_session() as session:
        await scan_ton(session)
        await scan_tron(session)

if __name__ == "__main__":
    asyncio.run(main())

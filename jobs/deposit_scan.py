from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from sqlalchemy import insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from database.db import get_session
from database import models
from services.referrals import pay_ref_bonuses

# ENV
TON_API_KEY  = os.getenv("TON_API_KEY")
TON_WALLET   = os.getenv("TON_WALLET")
TRON_API_KEY = os.getenv("TRON_API_KEY")
USDT_WALLET  = os.getenv("USDT_WALLET")

# окно просмотра (минуты)
SCAN_WINDOW_MIN = int(os.getenv("SCAN_WINDOW_MIN", "10"))

async def _get_settings(session: AsyncSession) -> models.Config | None:
    return await session.get(models.Config, 1)

async def _find_user_by_label(session: AsyncSession, label: str) -> Optional[models.User]:
    """
    Мэппинг label -> пользователь.
    1) Если label — это id депозита, берём deposit.user_id
    2) Иначе пробуем как telegram_id пользователя
    """
    # Попытка: label == deposit.id
    try:
        dep_id = int(label)
        dep = await session.get(models.Deposit, dep_id)
        if dep:
            user = await session.get(models.User, dep.user_id)
            if user:
                return user
    except Exception:
        pass

    # Попытка: label == telegram_id
    try:
        tg_id = int(label)
    except Exception:
        return None
    res = await session.execute(select(models.User).where(models.User.telegram_id == tg_id))
    return res.scalar_one_or_none()

async def _save_transaction_and_credit(
    session: AsyncSession,
    user: models.User,
    amount: float,
    currency: str,
    tx_hash: str,
    source: str,
    label: Optional[str],
) -> bool:
    """
    Идемпотентно добавляет транзакцию и пополняет баланс.
    Возвращает True, если зачисление прошло (не дубликат).
    """
    # Сначала вставка с защ. от дублей
    stmt = (
        insert(models.Transaction)
        .values(
            user_id=user.id,
            amount=float(amount),
            currency=currency,
            tx_hash=tx_hash,
            source=source,
            label=label,
            status="confirmed",
        )
        .prefix_with("ON CONFLICT (tx_hash) DO NOTHING")
    )
    res = await session.execute(stmt)

    # Если дубликат — rows==0
    if getattr(res, "rowcount", 0) == 0:
        await session.rollback()
        return False

    # Обновляем баланс
    if currency == "TON":
        user.balance_ton = float(user.balance_ton or 0) + float(amount)
    else:
        user.balance_usdt = float(user.balance_usdt or 0) + float(amount)

    await session.commit()
    return True

# ---------- TON ----------
async def scan_ton(session: AsyncSession) -> None:
    if not (TON_API_KEY and TON_WALLET):
        return
    since = datetime.now(timezone.utc) - timedelta(minutes=SCAN_WINDOW_MIN)

    # TonAPI пример; при необходимости подкорректируй путь/поля
    url = f"https://tonapi.io/v2/accounts/{TON_WALLET}/transactions?limit=100"  # входящие транзакции
    headers = {"Authorization": f"Bearer {TON_API_KEY}"}

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()

    items = data.get("transactions") or data.get("items") or []
    cfg = await _get_settings(session)
    min_dep = (cfg.min_deposit if cfg else 10.0)

    for tx in items:
        # приблизительный парсинг TonAPI (откорректируй по реальному ответу)
        ts = tx.get("utime") or tx.get("timestamp") or tx.get("time")
        if ts:
            dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
            if dt < since:
                continue
        inbound = (tx.get("in_msg") or tx.get("inMessage") or {})
        # адрес получателя должен быть наш
        # часть API даёт msg["destination"], часть — в другом поле; при необходимости подправь
        to_addr = (inbound.get("destination") or inbound.get("dst") or "").replace(" ", "")
        if to_addr and TON_WALLET and to_addr != TON_WALLET:
            continue

        tx_hash = tx.get("hash") or tx.get("transaction_id") or tx.get("id")
        if not tx_hash:
            continue

        # Сумма, нано-тоны → TON
        value = inbound.get("value") or inbound.get("amount") or 0
        try:
            amount = float(value) / 1e9
        except Exception:
            continue
        if amount <= 0 or amount < float(min_dep):
            continue

        # Label (comment/payload/message)
        label = (inbound.get("message") or inbound.get("comment") or inbound.get("payload") or "").strip()
        if not label:
            # Если не смогли извлечь label — пропустим (мы опираемся на label для связи с юзером)
            continue

        user = await _find_user_by_label(session, label)
        if not user or user.is_blocked:
            continue

        created = await _save_transaction_and_credit(
            session, user, amount, "TON", tx_hash, "TON", label
        )
        if created:
            # Реферальные бонусы
            await pay_ref_bonuses(session, user, amount, "TON")

# ---------- TRON / USDT TRC-20 ----------
async def scan_tron(session: AsyncSession) -> None:
    if not (TRON_API_KEY and USDT_WALLET):
        return
    since = datetime.now(timezone.utc) - timedelta(minutes=SCAN_WINDOW_MIN)

    # TronGrid пример: последние входящие TRC20 на адрес
    url = f"https://api.trongrid.io/v1/accounts/{USDT_WALLET}/transactions/trc20?limit=100&only_to=true"
    headers = {"TRON-PRO-API-KEY": TRON_API_KEY}

    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, headers=headers)
        r.raise_for_status()
        data = r.json()

    items = data.get("data", [])
    cfg = await _get_settings(session)
    min_dep = (cfg.min_deposit if cfg else 10.0)

    for tx in items:
        # Фильтр только USDT
        token_sym = ((tx.get("token_info") or {}).get("symbol") or "").upper()
        if token_sym != "USDT":
            continue

        # Время
        ts = tx.get("block_timestamp")
        if ts:
            dt = datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc)
            if dt < since:
                continue

        # Хеш и сумма
        tx_hash = tx.get("transaction_id")
        if not tx_hash:
            continue

        # USDT имеет 6 знаков после запятой
        try:
            amount = float(tx.get("value", 0)) / 1e6
        except Exception:
            continue
        if amount <= 0 or amount < float(min_dep):
            continue

        # Label из memo — у TronGrid формат может отличаться, подстрой по факту
        # Пробуем несколько полей:
        label = (tx.get("memo") or "").strip()
        if not label:
            # Иногда memo лежит в raw_data["data"] (hex/base64) — добавь свой декодер при необходимости
            raw_data = tx.get("raw_data") or {}
            raw_data_data = raw_data.get("data")
            if isinstance(raw_data_data, str):
                # часто это hex; если хочешь — декодируй здесь
                label = raw_data_data.strip()
        if not label:
            continue

        user = await _find_user_by_label(session, label)
        if not user or user.is_blocked:
            continue

        created = await _save_transaction_and_credit(
            session, user, amount, "USDT", tx_hash, "TRON", label
        )
        if created:
            await pay_ref_bonuses(session, user, amount, "USDT")

async def main():
    async with get_session() as session:
        await scan_ton(session)
        await scan_tron(session)

if __name__ == "__main__":
    asyncio.run(main())

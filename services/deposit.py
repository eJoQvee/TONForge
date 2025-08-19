from __future__ import annotations

import os
from typing import Literal, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from database import models
from utils.referrals import distribute_referral_income
from . import ton, usdt


Currency = Literal["TON", "USDT"]


async def create_deposit(
    session: AsyncSession,
    user_id: int,
    amount: float,
    currency: Currency,
) -> models.Deposit:
    """
    Создаёт запись депозита в НЕактивном состоянии.
    Активируется после подтверждения транзакции (см. check_deposit_status).
    В модели Deposit НЕТ поля address — адрес берём из настроек/ENV при выводе инструкции.
    """
    if currency not in ("TON", "USDT"):
        raise ValueError("Unsupported currency")

    # Проверим минимальный депозит из таблицы settings
    cfg = await session.get(models.Config, 1)
    min_dep = float(cfg.min_deposit if cfg else 10.0)
    if float(amount) < min_dep:
        raise ValueError(f"Минимальный депозит: {min_dep:g} {currency}")

    dep = models.Deposit(
        user_id=user_id,
        amount=float(amount),
        currency=currency,
        is_active=False,
    )
    session.add(dep)
    await session.commit()
    await session.refresh(dep)
    return dep


def deposit_label(dep: models.Deposit, fallback_user_tg_id: Optional[int] = None) -> str:
    """
    Метка для комментария (TON) / memo (USDT TRC-20).
    Рекомендуем использовать dep.id — коротко и уникально.
    """
    return str(dep.id)


async def check_deposit_status(session: AsyncSession, deposit_id: int) -> bool:
    """
    Опциональный «пассивный» чекер (если используешь не крон-сканер, а ручную проверку).
    - Для TON: services.ton.check_deposit(label, required_amount)
    - Для USDT(TRC20): services.usdt.check_deposit(to_address, label, required_amount)

    При подтверждении:
      - помечаем депозит активным
      - увеличиваем баланс пользователя
      - распределяем реферальный доход
    """
    dep = await session.get(models.Deposit, deposit_id)
    if not dep or dep.is_active:
        return False

    user = await session.get(models.User, dep.user_id)
    if not user or user.is_blocked:
        return False

    currency = dep.currency.upper()
    required = float(dep.amount)

    if currency == "TON":
        received = await ton.check_deposit(str(dep.id), required)
    else:
        # адрес берём из настроек/ENV (в модель его не записываем)
        to_addr = os.getenv("USDT_WALLET", "")
        if not to_addr:
            return False
        received = await usdt.check_deposit(to_addr, str(dep.id), required)

    if float(received) >= required:
        dep.is_active = True
        if currency == "TON":
            user.balance_ton = float(user.balance_ton or 0) + required
        else:
            user.balance_usdt = float(user.balance_usdt or 0) + required

        await distribute_referral_income(session, user.id, required, currency)
        await session.commit()
        return True

    return False

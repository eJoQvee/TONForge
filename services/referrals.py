from __future__ import annotations

from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import models

# Проценты уровней (можно вынести в таблицу settings позже)
LEVEL_PCTS = [0.10, 0.05, 0.03, 0.02, 0.01]  # 10 / 5 / 3 / 2 / 1 %

async def _get_user(session: AsyncSession, user_id: int) -> Optional[models.User]:
    return await session.get(models.User, user_id)

async def _get_upline(session: AsyncSession, user: models.User, depth: int = 5) -> List[models.User]:
    """
    Поднимаемся по цепочке referrer_id до depth уровней.
    Используем поле users.referrer_id (Invite-таблица не нужна для аплайна).
    """
    chain: List[models.User] = []
    current = user
    for _ in range(depth):
        if not current or not current.referrer_id:
            break
        ref = await session.get(models.User, current.referrer_id)
        if not ref:
            break
        chain.append(ref)
        current = ref
    return chain

async def pay_ref_bonuses(session: AsyncSession, depositor_user: models.User, amount: float, currency: str) -> None:
    """
    Начисляет бонусы 5 аплайнам за депозит depositor_user на amount.
    Пишем аудит в referral_payouts и сразу прибавляем к балансу реферера.
    """
    upline = await _get_upline(session, depositor_user, depth=len(LEVEL_PCTS))
    for level, ref_user in enumerate(upline, start=1):
        pct = LEVEL_PCTS[level - 1]
        bonus = float(amount) * pct
        # Балансы
        if currency.upper() == "TON":
            ref_user.balance_ton = float(ref_user.balance_ton or 0) + bonus
        else:
            ref_user.balance_usdt = float(ref_user.balance_usdt or 0) + bonus
        # Журнал
        payout = models.ReferralPayout(
            user_id=ref_user.id,
            from_user_id=depositor_user.id,
            level=level,
            amount=bonus,
            currency=currency.upper(),
        )
        session.add(payout)
    await session.commit()

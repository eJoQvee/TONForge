# services/referrals.py
from sqlalchemy import select
from database import models

# проценты уровней — можно вынести в settings
LEVEL_PCTS = [0.10, 0.05, 0.03, 0.02, 0.01]

async def pay_ref_bonuses(session, user: models.User, amount: float, currency: str):
    """
    Начисляет бонусы 5 уровням вверх по дереву (если есть).
    Денег на баланс — прямо сейчас (MVP), но лучше писать в отдельную таблицу referral_payouts.
    """
    cur = user
    for pct in LEVEL_PCTS:
        if not cur.referrer_id:
            break
        referrer = await session.get(models.User, cur.referrer_id)
        if not referrer:
            break
        bonus = amount * pct
        if currency == "TON":
            referrer.balance_ton = (referrer.balance_ton or 0) + bonus
        else:
            referrer.balance_usdt = (referrer.balance_usdt or 0) + bonus
        # можно записать лог в таблицу referral_payouts (если есть)
        await session.commit()
        cur = referrer

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import models


async def get_balance(session: AsyncSession, user_id: int) -> dict[str, float]:
    """Calculate current balance for a user.

    Sums deposits and withdrawals and returns a mapping
    of currency to balance.
    """
    deposit_stmt = (
        select(models.Deposit.currency, func.coalesce(func.sum(models.Deposit.amount), 0))
        .where(models.Deposit.user_id == user_id)
        .group_by(models.Deposit.currency)
    )
    withdrawal_stmt = (
        select(models.Withdrawal.currency, func.coalesce(func.sum(models.Withdrawal.amount), 0))
        .where(models.Withdrawal.user_id == user_id)
        .group_by(models.Withdrawal.currency)
    )

    balances: dict[str, float] = {}
    for currency, total in (await session.execute(deposit_stmt)).all():
        balances[currency] = total
    for currency, total in (await session.execute(withdrawal_stmt)).all():
        balances[currency] = balances.get(currency, 0) - total

    return balances


async def update_balance(session: AsyncSession, user_id: int) -> None:
    """Recalculate and update stored balance fields for the user."""
    balances = await get_balance(session, user_id)
    user = await session.get(models.User, user_id)
    if user is None:
        return
    user.balance_ton = balances.get("TON", 0)
    user.balance_usdt = balances.get("USDT", 0)
    await session.commit()

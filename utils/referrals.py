from sqlalchemy import select, func

from database.models import User, Deposit

REF_PERCENTS = [0.10, 0.05, 0.03, 0.02, 0.01]


async def add_referral(session, inviter_id: int, invitee_id: int) -> None:
    """Adds a referral relation between inviter and invitee."""
    if inviter_id == invitee_id:
        return
    invitee = await session.get(User, invitee_id)
    inviter = await session.get(User, inviter_id)
    if not invitee or not inviter or invitee.referrer_id:
        return
    invitee.referrer_id = inviter_id
    await session.commit()


def _invited_ids_query(user_id: int):
    return select(User.id).where(User.referrer_id == user_id)


async def get_referral_stats(session, user_id: int) -> dict:
    """Returns number of invitees and total referral bonuses."""
    invited_count = await session.scalar(
        select(func.count()).select_from(User).where(User.referrer_id == user_id)
    )

    deposit_sums = await session.execute(
        select(Deposit.currency, func.sum(Deposit.amount))
        .where(Deposit.user_id.in_(_invited_ids_query(user_id)))
        .group_by(Deposit.currency)
    )
    bonus_ton = bonus_usdt = 0.0
    for currency, total in deposit_sums:
        reward = total * REF_PERCENTS[0]
        if currency == "TON":
            bonus_ton = reward
        else:
            bonus_usdt = reward

    return {"invited": invited_count, "bonus_ton": bonus_ton, "bonus_usdt": bonus_usdt}


async def distribute_referral_income(session, user_id: int, amount: float, currency: str) -> None:
    """Distributes referral rewards up to 5 levels."""
    current_id = user_id
    for percent in REF_PERCENTS:
        user = await session.get(User, current_id)
        if not user or not user.referrer_id:
            break
        ref = await session.get(User, user.referrer_id)
        reward = amount * percent
        if currency == "TON":
            ref.balance_ton += reward
        else:
            ref.balance_usdt += reward
        current_id = ref.id

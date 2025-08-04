REF_PERCENTS = [0.10, 0.05, 0.03, 0.02, 0.01]


async def distribute_referral_income(session, user_id: int, amount: float, currency: str):
    """
    Распределяет реферальное вознаграждение по цепочке до 5 уровней.
    """
    current_id = user_id
    for level, percent in enumerate(REF_PERCENTS, start=1):
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

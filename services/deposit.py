from database import models
from services import ton, usdt


async def create_deposit(session, user_id: int, amount: float, currency: str) -> models.Deposit:
    """Create a new deposit record in the database.

    The deposit is created in an inactive state. It will be activated once the
    corresponding blockchain transaction is confirmed.
    """
    deposit = models.Deposit(
        user_id=user_id, amount=amount, currency=currency, is_active=False
    )
    session.add(deposit)
    await session.commit()
    await session.refresh(deposit)
    return deposit


async def check_deposit_status(session, deposit_id: int) -> bool:
    """Check deposit confirmations and update user balance.

    Depending on the deposit currency, calls either ``services.ton`` or
    ``services.usdt`` to verify that the deposit transaction has been
    confirmed. If the required amount is received, the deposit becomes active
    and the user's balance is increased by the deposit amount.

    Returns ``True`` if the deposit was confirmed and the balance updated,
    otherwise ``False``.
    """
    deposit = await session.get(models.Deposit, deposit_id)
    if not deposit or deposit.is_active:
        return False

    user = await session.get(models.User, deposit.user_id)
    if not user:
        return False

    if deposit.currency.upper() == "TON":
        received = await ton.check_deposit(str(deposit.id), deposit.amount)
    else:
        address = getattr(deposit, "address", "")
        received = await usdt.check_deposit(address, str(deposit.id), deposit.amount)

    if received >= deposit.amount:
        deposit.is_active = True
        if deposit.currency.upper() == "TON":
            user.balance_ton += deposit.amount
        else:
            user.balance_usdt += deposit.amount
        await session.commit()
        return True

    return False

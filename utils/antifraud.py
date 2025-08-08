"""Basic anti-fraud helpers."""

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import models


async def check_and_update_ip(
    session: AsyncSession, user: models.User, ip: str | None
) -> None:
    """Store user's IP and block if duplicates are found.

    If another account already uses the same IP, mark the current user as
    blocked. The function commits the session after updating the user.
    """

    if not ip:
        return

    user.last_ip = ip

    result = await session.execute(
        select(func.count(models.User.id)).where(
            models.User.last_ip == ip, models.User.id != user.id
        )
    )
    duplicates = result.scalar_one()
    if duplicates:
        user.is_blocked = True

    await session.commit()

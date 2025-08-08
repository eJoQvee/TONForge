import asyncio
from sqlalchemy import inspect, text
from database.db import engine
from database import models


async def migrate() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

        def has_is_blocked_column(sync_conn):
            inspector = inspect(sync_conn)
            columns = [col["name"] for col in inspector.get_columns("users")]
            return "is_blocked" in columns

        if not await conn.run_sync(has_is_blocked_column):
            await conn.execute(text("ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE"))

        # ensure settings row exists
        count = await conn.scalar(text("SELECT COUNT(*) FROM settings"))
        if count == 0:
            await conn.execute(
                text(
                    "INSERT INTO settings (id, daily_percent, min_deposit, min_withdraw, withdraw_delay_hours, notification_text)"
                    " VALUES (1, 0.023, 10, 50, 24, '')"
                )
            )


if __name__ == "__main__":
    asyncio.run(migrate())

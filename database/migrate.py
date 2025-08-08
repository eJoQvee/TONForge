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


if __name__ == "__main__":
    asyncio.run(migrate())

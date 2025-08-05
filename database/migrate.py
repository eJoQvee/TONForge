import asyncio
from database.db import engine
from database import models


async def migrate() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(migrate())

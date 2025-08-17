# database/migrate.py
import asyncio

# импорт моделей, чтобы зарегистрировать таблицы
try:
    from database import models as _models  # noqa: F401
except Exception:
    pass

from database.db import engine, Base

async def run():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run())

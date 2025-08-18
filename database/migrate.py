import asyncio
from sqlalchemy import inspect, text
from importlib import import_module

from database.db import engine, Base
from database import models

def _import_models():
    """
    Импортируй ВСЕ свои модели, чтобы Base.metadata их увидела.
    Подстрой список под свой проект, если у тебя иные файлы.
    """
    candidates = (
        "database.models",              # если есть сборщик
        "database.models.user",
        "database.models.deposit",
        "database.models.transaction",
        "database.models.referral",
    )
    for mod in candidates:
        try:
            import_module(mod)
        except Exception:
            pass

async def _run_async():
    _import_models()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

def migrate():
    """
    Можно вызывать импортом: from database.migrate import migrate
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(_run_async())
    else:
        return asyncio.create_task(_run_async())

if __name__ == "__main__":
    asyncio.run(_run_async())
